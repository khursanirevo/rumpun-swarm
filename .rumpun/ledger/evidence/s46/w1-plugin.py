r"""rumpun plugin — the pack format and the publish guardrails.

Operator directive (direct ledger seq 2, 2026-09-15): packs carry priors/ only
— general knowledge: templates, prompts, lint profile, routes, patterns —
and campaign/ content never installs or publishes. ``rumpun plugin lint``
rejects sids, absolute paths, and private-vocabulary matches at publish.
Hub v1 is git-based sharing (pack = repo, publish = push, install = pull +
digest verify); the digest is format-checked here and content-verified at
install time by plugin_install, the hub arc's install step (s46).

Pack layout::

    <pack>/
      manifest.yaml
      priors/    content class: installs and publishes
      campaign/  content class: never installs, never publishes

The installer's discovery reads priors/ only — structurally: no code path in
this module walks campaign/, so campaign content is invisible to every
install and publish consumer regardless of its contents.

Manifest schema (manifest.yaml, house YAML via rumpun.yamlio)::

    name: kaggle-base        # required, ^[a-z0-9][a-z0-9_-]*$
    version: 0.1.0           # required, ^\d+\.\d+\.\d+$
    base: other-pack         # optional: lineage parent; absent = the pack IS a base
    digest: <64 hex>         # required, ^[0-9a-f]{64}$ — content digest of the
                             # priors/ tree; format checked at lint, content
                             # verified at install (hub v1)
    private_vocabulary:      # required, non-empty list of word-like terms
      - term                 # ^[A-Za-z0-9][A-Za-z0-9_-]*$, 1-64 chars
    source: provenance note  # required, non-empty string

Unknown manifest keys are violations (strict v1 schema). Manifest text values
are not content-scanned: the sid/absolute-path/private-vocabulary rejections
guard the priors/ tree, which is what installs and publishes.
"""

from __future__ import annotations

import fcntl
import hashlib
import logging
import os
import re
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from rumpun import scaffold, yamlio

logger = logging.getLogger(__name__)

MANIFEST_NAME = "manifest.yaml"
PRIORS_DIRNAME = "priors"
CAMPAIGN_DIRNAME = "campaign"

# Content classes: priors/ installs and publishes; campaign/ never does. The
# names are the directory names inside a pack.
PACK_CLASSES: dict[str, str] = {
    "priors": "installs and publishes",
    "campaign": "never installs, never publishes",
}

# A sid token: s followed by digits on word boundaries, so "runs12" and
# "status3" never match while "s36", "s44/w1" (path parts), and "s36-gate" do.
SID_TOKEN_RE = re.compile(r"\bs\d+\b")

# Absolute-path tokens. POSIX: a slash-led path whose leading slash is not
# preceded by a word char, dot, colon, or another slash — multi-segment URLs
# (scheme://host/x) never match, relative paths (a/b) never match, and
# single-segment names (/name) do. Windows: X:\dir\file and X:/dir/file.
ABS_PATH_RE = re.compile(r"(?<![\w.:/])/(?:[\w.-]+/)*[\w.-]+")
WIN_PATH_RE = re.compile(r"(?<!\w)[A-Za-z]:[\\/](?:[\w.-]+[\\/])*[\w.-]+")

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
TERM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
TERM_MAX = 64

REQUIRED_KEYS = ("name", "version", "digest", "private_vocabulary", "source")
OPTIONAL_KEYS = ("base",)


class PluginError(Exception):
    """Structural pack trouble: missing or invalid manifest.yaml."""


@dataclass
class PackFinding:
    """One lint result; message embeds "path:line" so offenses are named.

    path is pack-relative; line is the 1-based content line, 0 for filename
    offenses, 1 for missing-manifest and missing-key offenses (the manifest's
    first line is named so the offense always carries file and line).
    """

    severity: str  # "error" | "warning"
    message: str
    path: str = ""
    line: int = 0


def load_manifest(pack_dir: Path) -> dict[str, Any]:
    """Load manifest.yaml from the pack directory (house YAML, strict keys)."""
    mpath = Path(pack_dir) / MANIFEST_NAME
    if not mpath.is_file():
        msg = f"{mpath}: no {MANIFEST_NAME}; a pack is a directory with {MANIFEST_NAME} and priors/"
        raise PluginError(msg)
    try:
        return yamlio.load(mpath)  # strict: duplicate and non-string keys rejected
    except yamlio.YamlError as exc:
        msg = f"{mpath}: invalid manifest: {exc}"
        raise PluginError(msg) from exc


def _key_line(manifest_text: str, key: str) -> int:
    """1-based line of "key:" in the raw manifest text; 1 when absent."""
    for lineno, line in enumerate(manifest_text.splitlines(), 1):
        if re.match(rf"^\s*{re.escape(key)}\s*:", line):
            return lineno
    return 1


def _manifest_findings(pack_dir: Path, manifest: Any, manifest_text: str) -> list[PackFinding]:
    findings: list[PackFinding] = []
    if not (Path(pack_dir) / MANIFEST_NAME).is_file():
        findings.append(
            PackFinding(
                "error",
                f"{MANIFEST_NAME}:1: missing {MANIFEST_NAME} — a pack is a directory with "
                f"{MANIFEST_NAME} and priors/",
                path=MANIFEST_NAME,
                line=1,
            )
        )
        return findings

    def err(message: str, key: str, line: int | None = None) -> None:
        lineno = line if line is not None else _key_line(manifest_text, key)
        findings.append(
            PackFinding(
                "error",
                f"{MANIFEST_NAME}:{lineno}: {message}",
                path=MANIFEST_NAME,
                line=lineno,
            )
        )

    if not isinstance(manifest, dict):
        err(f"manifest must be a mapping, got {type(manifest).__name__}", "name")
        return findings

    for key in REQUIRED_KEYS:
        if key not in manifest:
            err(f"missing required key {key!r}", key, line=1)
    for key in manifest:
        if key not in REQUIRED_KEYS and key not in OPTIONAL_KEYS:
            err(f"unknown manifest key {key!r} (strict v1 schema)", key)

    name = manifest.get("name")
    if name is not None and (not isinstance(name, str) or not NAME_RE.match(name)):
        err(f"name must match ^[a-z0-9][a-z0-9_-]*$, got {name!r}", "name")
    version = manifest.get("version")
    if version is not None and (not isinstance(version, str) or not VERSION_RE.match(version)):
        err(f"version must match ^\\d+\\.\\d+\\.\\d+$, got {version!r}", "version")
    digest = manifest.get("digest")
    if digest is not None and (not isinstance(digest, str) or not DIGEST_RE.match(digest)):
        err(f"digest must be 64 hex chars, got {digest!r}", "digest")
    source = manifest.get("source")
    if source is not None and (not isinstance(source, str) or not source.strip()):
        err("source must be a non-empty provenance note", "source")

    vocab = manifest.get("private_vocabulary")
    if vocab is not None:
        if not isinstance(vocab, list) or not vocab:
            err("private_vocabulary must be a non-empty list of terms", "private_vocabulary")
        else:
            for index, term in enumerate(vocab):
                if (
                    not isinstance(term, str)
                    or not term
                    or not TERM_RE.match(term)
                    or len(term) > TERM_MAX
                ):
                    err(
                        f"private_vocabulary[{index}] must be a word-like term "
                        f"(^[A-Za-z0-9][A-Za-z0-9_-]*$, 1-{TERM_MAX} chars), got {term!r}",
                        "private_vocabulary",
                    )

    base = manifest.get("base")
    if base is not None:
        if not isinstance(base, str) or not NAME_RE.match(base):
            err(f"base must match ^[a-z0-9][a-z0-9_-]*$, got {base!r}", "base")
        elif name and base == name:
            err(f"base must differ from the pack's own name {name!r}", "base")
    return findings


def _vocab_pattern(terms: Any) -> re.Pattern[str] | None:
    """Case-insensitive word-anchored alternation over schema-valid terms only."""
    usable = sorted(
        (
            t
            for t in terms or []
            if isinstance(t, str) and TERM_RE.match(t) and len(t) <= TERM_MAX
        ),
        key=len,
        reverse=True,
    )
    if not usable:
        return None
    return re.compile(
        rf"\b(?:{'|'.join(re.escape(t) for t in usable)})\b", re.IGNORECASE
    )


def _name_findings(rel: str, vocab: re.Pattern[str] | None) -> list[PackFinding]:
    """Offenses visible in the pack-relative filename itself (line 0)."""
    out: list[PackFinding] = []
    for hit in SID_TOKEN_RE.finditer(rel):
        out.append(
            PackFinding(
                "error",
                f"{rel} (filename): sid token {hit.group()!r} — season references are "
                "campaign-private and never publish",
                path=rel,
                line=0,
            )
        )
    if vocab is not None:
        for hit in vocab.finditer(rel):
            out.append(
                PackFinding(
                    "error",
                    f"{rel} (filename): private-vocabulary match {hit.group()!r} — packs "
                    "speak general knowledge",
                    path=rel,
                    line=0,
                )
            )
    return out


def _line_findings(
    rel: str, lineno: int, text: str, vocab: re.Pattern[str] | None
) -> list[PackFinding]:
    """Offenses on one content line; the message names the file and the line."""
    out: list[PackFinding] = []

    def add(match: re.Match[str], kind: str, why: str) -> None:
        out.append(
            PackFinding(
                "error",
                f"{rel}:{lineno}: {kind} {match.group()!r} — {why}",
                path=rel,
                line=lineno,
            )
        )

    for hit in SID_TOKEN_RE.finditer(text):
        add(hit, "sid token", "season references are campaign-private and never publish")
    if vocab is not None:
        for hit in vocab.finditer(text):
            add(hit, "private-vocabulary match", "packs speak general knowledge")
    for hit in ABS_PATH_RE.finditer(text):
        add(hit, "absolute path", "packs carry relative paths only")
    for hit in WIN_PATH_RE.finditer(text):
        add(hit, "absolute path", "packs carry relative paths only")
    return out


def _content_findings(pack_dir: Path, manifest: Any) -> list[PackFinding]:
    findings: list[PackFinding] = []
    priors = Path(pack_dir) / PRIORS_DIRNAME
    if not priors.is_dir():
        findings.append(
            PackFinding(
                "warning",
                f"pack carries no {PRIORS_DIRNAME}/ tree: nothing installs or publishes",
            )
        )
    if not isinstance(manifest, dict):
        return findings
    vocab = _vocab_pattern(manifest.get("private_vocabulary"))
    # Discovery and lint both stay inside priors/ — campaign/ is never walked.
    for path in sorted(priors.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(pack_dir).as_posix()
        findings.extend(_name_findings(rel, vocab))
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            logger.exception("cannot read pack file %s", path)
            findings.append(
                PackFinding(
                    "error",
                    f"{rel}: unreadable file — publish needs every priors/ file readable",
                    path=rel,
                    line=0,
                )
            )
            continue
        for lineno, line_text in enumerate(lines, 1):
            findings.extend(_line_findings(rel, lineno, line_text, vocab))
    return findings


def discover_priors(pack_dir: Path) -> list[Path]:
    """The installer's discovery: file paths under priors/ only, sorted.

    campaign/ is structurally invisible: the walk never leaves priors/, so
    campaign content (sids, secrets) can never appear in an install set.
    """
    priors = Path(pack_dir) / PRIORS_DIRNAME
    if not priors.is_dir():
        return []
    return sorted(p for p in priors.rglob("*") if p.is_file())


def plugin_lint(pack_dir: Path, manifest: dict[str, Any]) -> list[PackFinding]:
    """Lint a pack for publish: manifest schema plus priors/ content rules.

    manifest is the loaded manifest.yaml mapping (load_manifest raises
    PluginError for a missing or invalid file). Errors are publish
    rejections: sids, absolute paths, private-vocabulary matches, manifest
    violations — each finding's message names the pack-relative file and the
    1-based line. The pack directory itself is never mutated.
    """
    pack_dir = Path(pack_dir)
    findings: list[PackFinding] = []
    manifest_text = ""
    mpath = pack_dir / MANIFEST_NAME
    if mpath.is_file():
        try:
            manifest_text = mpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            logger.exception("cannot read manifest %s", mpath)
    findings.extend(_manifest_findings(pack_dir, manifest, manifest_text))
    findings.extend(_content_findings(pack_dir, manifest))
    return findings


# --- s46 install/list/use (the hub arc's install step) -----------------------

def plugins_dir(root: Path) -> Path:
    """The campaign's installed-plugin tree: <root>/plugins/<name>/priors/."""
    return Path(root) / "plugins"


def plugins_registry_path(root: Path) -> Path:
    """The campaign's plugins.yml: install records keyed by pack name."""
    return Path(root) / scaffold.RUMPUN_DIR / "plugins.yml"


def priors_digest(priors_dir: Path) -> str:
    """sha256 over a priors/ tree: (rel path, NUL, file bytes, NUL)
    triplets in sorted relative-path order, POSIX separators. An empty tree
    hashes as sha256 of empty input. The digest a manifest seals and
    plugin_install verifies.
    """
    priors_dir = Path(priors_dir)
    digest = hashlib.sha256()
    for path in sorted(p for p in priors_dir.rglob("*") if p.is_file()):
        digest.update(path.relative_to(priors_dir).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _registry_load(reg_path: Path) -> dict[str, Any]:
    """Read plugins.yml: {} when absent; PluginError on malformed content."""
    if not reg_path.is_file():
        return {}
    try:
        data = yamlio.load(reg_path)  # strict: dup and non-string keys rejected
    except yamlio.YamlError as exc:
        msg = f"{reg_path}: unreadable plugins registry: {exc}"
        raise PluginError(msg) from exc
    if not isinstance(data, dict) or not isinstance(data.get("plugins"), dict):
        raise PluginError(f"{reg_path}: registry must carry a 'plugins' mapping")
    for entry_name, record in data["plugins"].items():
        if not isinstance(record, dict):
            msg = f"{reg_path}: registry entry {entry_name!r} must be a mapping"
            raise PluginError(msg)
    return data["plugins"]


def _registry_write(reg_path: Path, plugins: dict[str, Any]) -> None:
    """Atomic replace of plugins.yml; the caller holds the flock."""
    text = yaml.safe_dump({"plugins": plugins}, sort_keys=False, allow_unicode=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=reg_path.parent, prefix=".plugins-", suffix=".yml.tmp"
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, reg_path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _registry_update(root: Path, name: str, record: dict[str, Any]) -> None:
    """Read-modify-write of plugins.yml under an exclusive flock on
    .rumpun/plugins.lock, so concurrent installs never lose a record."""
    reg_path = plugins_registry_path(root)
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = reg_path.parent / "plugins.lock"
    with lock_path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            plugins = _registry_load(reg_path)
            plugins[name] = record
            _registry_write(reg_path, plugins)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def plugin_install(root: Path, pack_dir: Path) -> dict[str, Any]:
    """Install a pack into the campaign rooted at root.

    Gates, each refusing with PluginError naming the pack:
      1. manifest.yaml loads (load_manifest).
      2. schema-valid name (an install needs an install target).
      3. digest: the manifest digest equals priors_digest() over the pack's
         priors/ tree; a tampered pack (edited after sealing) mismatches.
      4. plugin_lint: any error finding refuses the install.
    priors/ then copies into <root>/plugins/<name>/priors/ through a
    staging directory re-digested before the atomic rename; the staging
    self-check catches a source mutated mid-copy. campaign/ is structurally
    invisible: the copy walks discover_priors() (priors-only), so campaign
    content never reaches the campaign tree. Re-install replaces the previous
    tree only after the new copy verifies. The install record lands in
    <root>/.rumpun/plugins.yml under an exclusive flock, atomic replace.
    """
    root = Path(root)
    pack_dir = Path(pack_dir)
    manifest = load_manifest(pack_dir)
    name = manifest.get("name") if isinstance(manifest, dict) else None
    if not isinstance(name, str) or not NAME_RE.match(name):
        msg = f"{pack_dir}: pack refused: manifest carries no schema-valid name"
        raise PluginError(msg)
    declared = manifest.get("digest")
    actual = priors_digest(pack_dir / PRIORS_DIRNAME)
    if declared != actual:
        msg = (
            f"pack {name!r} refused: digest mismatch: manifest declares {declared!r}, "
            f"the priors/ tree hashes to {actual}"
        )
        raise PluginError(msg)
    findings = plugin_lint(pack_dir, manifest)
    errors = [f for f in findings if f.severity == "error"]
    for finding in errors:
        logger.error("plugin install: %s: %s", name, finding.message)
    if errors:
        msg = f"pack {name!r} refused: {len(errors)} lint error(s), see the logged findings"
        raise PluginError(msg)
    dest_root = plugins_dir(root)
    dest_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(dir=dest_root, prefix=f".{name}.staging-"))
    try:
        for path in discover_priors(pack_dir):
            rel = path.relative_to(pack_dir / PRIORS_DIRNAME)
            target = staging / PRIORS_DIRNAME / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        staged = priors_digest(staging / PRIORS_DIRNAME)
        if staged != declared:
            msg = f"pack {name!r} refused: priors/ mutated during install (staged {staged})"
            raise PluginError(msg)
        dest = dest_root / name
        if dest.exists():
            shutil.rmtree(dest)
        os.replace(staging, dest)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    record = {
        "version": manifest.get("version", ""),
        "digest": declared,
        "installed_at": time.time(),
        "source": manifest.get("source", ""),
    }
    _registry_update(root, name, record)
    logger.info("installed pack %r (%s) into %s", name, record["version"], dest)
    return {"name": name, **record}


def plugin_list(root: Path) -> list[dict[str, Any]]:
    """Installed packs from .rumpun/plugins.yml: name, version, digest (plus
    installed_at, source), sorted by name. No registry -> empty list."""
    plugins = _registry_load(plugins_registry_path(root))
    return [{"name": name, **record} for name, record in sorted(plugins.items())]


def resolve_template(root: Path, plugins: list[str], rel: str) -> str | None:
    """First installed pack carrying priors/<rel>, over plugins in order.

    rel is the scaffold output path relative to .rumpun/ (e.g.
    "prompts/base/execute.md"); the pack carries it at priors/<rel>. None
    when no pack carries it. A named plugin that is not installed raises
    PluginError naming it; never silently skipped.
    """
    root = Path(root)
    installed = {record["name"] for record in plugin_list(root)}
    for name in plugins:
        if name not in installed:
            msg = f"plugin {name!r} is not installed; 'rumpun plugin install' it first"
            raise PluginError(msg)
        candidate = plugins_dir(root) / name / PRIORS_DIRNAME / rel
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    return None


def init_project(target: Path, plugins: list[str] | None = None) -> None:
    """Scaffold a rumpun project; templates/prompts resolve from installed
    packs before the base tree.

    plugins empty: scaffold.init_project verbatim. Otherwise every scaffold
    output (rumpun.yaml, seasons, prompts/base/*.md, README, ledger and runs
    keepers) resolves from priors/<same .rumpun-relative path> of the first
    pack carrying it, falling back to the base tree. Uninstalled names fail
    before anything is written. The overwrite guard matches plain init.
    """
    target = Path(target)
    plugins = list(plugins or [])
    if not plugins:
        scaffold.init_project(target)
        return
    installed = {record["name"] for record in plugin_list(target)}
    for name in plugins:
        if name not in installed:
            msg = f"plugin {name!r} is not installed; 'rumpun plugin install' it first"
            raise PluginError(msg)
    if (target / scaffold.RUMPUN_DIR / "rumpun.yaml").exists():
        msg = f"{target} already has .rumpun/rumpun.yaml — init refuses to overwrite"
        raise scaffold.ScaffoldError(msg)
    base_plan = [
        ("rumpun.yaml", scaffold.RUMPUN_YAML),
        ("seasons/s1.yaml", scaffold.SEASON_S1),
        ("seasons/_template.yaml", scaffold.SEASON_TEMPLATE),
        ("README.md", scaffold.README),
        ("ledger/.gitkeep", ""),
        ("runs/.gitignore", "*\n!.gitignore\n"),
    ]
    base_plan.extend(
        (f"prompts/base/{phase}.md", body) for phase, body in scaffold.PROMPTS.items()
    )
    for rel, base in base_plan:
        content = base
        for name in plugins:
            candidate = plugins_dir(target) / name / PRIORS_DIRNAME / rel
            if candidate.is_file():
                content = candidate.read_text(encoding="utf-8")
                break
        scaffold._write(target / scaffold.RUMPUN_DIR / rel, content)
