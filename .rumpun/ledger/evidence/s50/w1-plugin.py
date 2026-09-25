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
    """The campaign's installed-plugin tree: <root>/.rumpun/plugins/<name>/."""
    return Path(root) / scaffold.RUMPUN_DIR / "plugins"


def plugins_registry_path(root: Path) -> Path:
    """The campaign's plugins.yml: install records keyed by pack name."""
    return Path(root) / scaffold.RUMPUN_DIR / "plugins.yml"


def priors_digest(pack_dir: Path) -> str:
    """sha256 over the pack's priors/ tree, the digest a manifest seals.

    Stream per file, in sorted pack-relative POSIX-path order (the path
    includes the priors/ prefix): rel path, NUL, file bytes, no trailing
    separator (the s46w2 pinned convention). An empty or missing priors/
    tree hashes as sha256 of empty input. plugin_install verifies the
    manifest digest against this; the pins' helper computes it
    independently and must agree.
    """
    pack_dir = Path(pack_dir)
    digest = hashlib.sha256()
    priors = pack_dir / PRIORS_DIRNAME
    for path in sorted(p for p in priors.rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack_dir).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
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
    Then manifest.yaml and priors/ copy into <root>/.rumpun/plugins/<name>/
    through a staging directory that is re-digested before the atomic
    rename; the staging self-check catches a source mutated mid-copy.
    campaign/ is structurally invisible: the copy walks discover_priors()
    (priors-only), so campaign content never reaches the campaign tree.
    The installed manifest.yaml doubles as the install record (name,
    version, digest under .rumpun/plugins/<name>/, outside priors/); the
    registry row also lands in <root>/.rumpun/plugins.yml under an
    exclusive flock, atomic replace. Re-install replaces the previous tree
    only after the new copy verifies.
    """
    root = Path(root)
    pack_dir = Path(pack_dir)
    manifest = load_manifest(pack_dir)
    name = manifest.get("name") if isinstance(manifest, dict) else None
    if not isinstance(name, str) or not NAME_RE.match(name):
        msg = f"{pack_dir}: pack refused: manifest carries no schema-valid name"
        raise PluginError(msg)
    declared = manifest.get("digest")
    actual = priors_digest(pack_dir)
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
        shutil.copyfile(pack_dir / MANIFEST_NAME, staging / MANIFEST_NAME)
        for path in discover_priors(pack_dir):
            rel = path.relative_to(pack_dir / PRIORS_DIRNAME)
            target = staging / PRIORS_DIRNAME / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        staged = priors_digest(staging)
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


def resolve_prompt(root: Path, rel: str) -> Path | None:
    """First installed pack carrying priors/<rel>, over the base tree.

    root is the campaign's .rumpun dir; installed packs live at
    root/plugins/<name>/. Pack dirs are tried in sorted-name order; the
    first whose priors tree carries <rel> wins (pack before base). The
    fallback is the campaign file root/<rel>; None when neither has it.
    (s46w2 pinned interface; supersedes s46 w1's resolve_template.)
    """
    root = Path(root)
    packs = sorted(p for p in (root / "plugins").glob("*") if p.is_dir())
    for pack_dir in packs:
        candidate = pack_dir / PRIORS_DIRNAME / rel
        if candidate.is_file():
            return candidate
    fallback = root / rel
    return fallback if fallback.is_file() else None


def _seed_season(season_path: Path, pack_name: str) -> None:
    """Fill empty goal/metric in a freshly scaffolded seed season so the
    pack-scaffolded campaign lints clean (s46w2 pin 4; the s46 band repro).
    Only empty fields are touched; a pack-provided s1.yaml carrying both
    filled passes through unchanged.
    """
    season = yamlio.load(season_path)
    goal = str(season.get("goal") or "").strip()
    metric = str(season.get("metric") or "").strip()
    if goal and metric:
        return
    if not goal:
        season["goal"] = f"Adopt the {pack_name} pack as the campaign base"
    if not metric:
        season["metric"] = f"{pack_name} seed season verdict recorded"
    season_path.write_text(
        yaml.safe_dump(season, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    logger.info("seeded empty goal/metric in %s from pack %r", season_path, pack_name)


def init_project(target: Path, plugins: list[str] | None = None) -> None:
    """Scaffold a rumpun project; each --plugin names a PACK DIRECTORY.

    Every pack is installed into the target campaign first (plugin_install:
    digest-verified, lint-gated, priors/ only). Then every scaffold output
    (rumpun.yaml, seasons, prompts/base/*.md, README, ledger and runs
    keepers) resolves from priors/<same .rumpun-relative path> of the first
    installed pack carrying it, falling back to the base tree. A seed
    season left with empty goal/metric is seeded from the first pack's
    name so the scaffolded campaign lints clean (the s46 band repro). No
    packs: scaffold.init_project verbatim. The overwrite guard runs before
    any write or install.
    """
    target = Path(target)
    pack_dirs = [Path(p) for p in (plugins or [])]
    if not pack_dirs:
        scaffold.init_project(target)
        return
    dot = target / scaffold.RUMPUN_DIR
    if (dot / "rumpun.yaml").exists():
        msg = f"{target} already has .rumpun/rumpun.yaml — init refuses to overwrite"
        raise scaffold.ScaffoldError(msg)
    names = [plugin_install(target, pack_dir)["name"] for pack_dir in pack_dirs]
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
        found = resolve_prompt(dot, rel)
        content = found.read_text(encoding="utf-8") if found else base
        scaffold._write(dot / rel, content)
    _seed_season(dot / "seasons" / "s1.yaml", names[0])


# --- s50 distill: the flywheel's export ---------------------------------------

# The distilled gates. Each body is a FIXED generalized text, hand-distilled
# from the campaign's ratified records into a campaign-agnostic prior: no
# season identifiers, no campaign names, no paths. The distill's scan only
# decides WHICH gates are evidenced in a campaign's ratified records; it
# never rewrites the text, so the output cannot leak campaign-private
# content by construction.

def _evidence(*patterns: str) -> tuple[re.Pattern[str], ...]:
    """Compile gate-evidence patterns, case-insensitive over the corpus."""
    return tuple(re.compile(p, re.IGNORECASE) for p in patterns)


@dataclass(frozen=True)
class DistilledPrior:
    """One proven gate as a distillable prior.

    key — priors/<key>.md in the emitted pack
    title — the prior's one-line name (the body's heading)
    evidence — any corpus match evidences the gate in this campaign
    body — the generalized prior text (campaign-agnostic by construction)
    """

    key: str
    title: str
    evidence: tuple[re.Pattern[str], ...]
    body: str


DISTILLED_PRIORS: tuple[DistilledPrior, ...] = (
    DistilledPrior(
        key="falsify-enforcement",
        title="Seal the kill test before the run",
        evidence=_evidence(r"falsification", r"\bfalsify\b"),
        body="""\
# Seal the kill test before the run

## The prior

Before any execution that could be reported as a success, seal a
falsification record: comparator, metric, threshold, dataset, confidence.
The seal happens before execution; a kill test written after the result is
not a seal.

## Why this holds

Vacuous kill tests ("the script runs", "the loss went down") are the
failure mode: they pass on anything, so they prove nothing. A record
sealed before the run cannot be shaped to flatter the result. The
strongest form is a detector that falsifies its own premise: it can come
back with the premise dead, and that still counts, because the sealed
record is what makes the negative outcome evidence.

## How to apply

- Every claimed improvement names, in advance, the test that would kill it.
- The record carries comparator, metric, threshold, dataset, confidence.
- Verdict classes: kill, revise, retain, inconclusive; every verdict names
  its consequence.
- An evaluator's written verdict is a claim, not independent proof; weight
  travels with independent artifact checks. A negative outcome with a
  sealed record outranks a positive outcome without one.
""",
    ),
    DistilledPrior(
        key="band-mask-guard",
        title="A win must not stand on a masked band",
        evidence=_evidence(r"band[ -]masked", r"LOSS-band", r"band_mask"),
        body="""\
# A win must not stand on a masked band

## The prior

A verdict's band is written before the run: WIN when specific, checkable
clauses are met. Losses are recorded with the same care as wins. When a
unit records a loss while the same unit shipped integrated deliverables,
the band definition, not the work, is what failed: the band masked
delivered value. Recalibrate the band; do not re-grade the work.

## Why this holds

The mask works in both directions. A loss that shipped integrated modules
means the band under-counted delivered value. A win whose clauses a
vacuous test satisfies means the band over-counted. Either direction, the
repair is recalibration with evidence, recorded as its own verdict.

## How to apply

- Bands are specific: N clauses, each independently checkable after the
  run, written before the run.
- A loss still ships, and records what its work implies for the next
  iteration; a failed unit can still earn its WIN band when the clauses
  are met.
- Seeing "loss shipped integrated deliverables" arms a band-calibration
  finding; repair the band with evidence, then continue.
""",
    ),
    DistilledPrior(
        key="stall-resume",
        title="Judge stall on durable progress, resume from the salvage",
        evidence=_evidence(r"stopped_stall", r"stall rule", r"durable progress"),
        body="""\
# Judge stall on durable progress, resume from the salvage

## The prior

Stall detection keys on harness-observed durable progress: new artifact
content, appended bytes, accepted checkpoint, state transition. Heartbeats,
repeated log lines, and file mtimes do not count. Liveness (a process that
exists) is not progress. A stalled unit is stopped on that evidence, and
the work resumes from the last accepted checkpoint or the recorded
salvage, never from zero.

## Why this holds

The classic bug: a stall rule that measured runtime instead of progress
killed writers that were mid-write; the fix shipped with a regression
test, and the killed season's salvage seeded the landing. The inverse bug
is as real: a writer frozen mid-write looks alive to any liveness check.
Appended bytes and new artifact content are the signals that survive
both.

## How to apply

- Size the stall window to the task; one window does not fit all writes.
- Detection thresholds ship with a regression test, always.
- After a stop, harvest the salvage first; the next attempt starts from
  it.
""",
    ),
    DistilledPrior(
        key="drift-retirement",
        title="A moved assumption re-seals; it is never silently dropped",
        evidence=_evidence(r"\bDRIFT\b", r"drift mismatch", r"re-seal"),
        body="""\
# A moved assumption re-seals; it is never silently dropped

## The prior

A sealed repro pins assumptions about current behavior. When the main
line moves and the repro's assumptions no longer hold, the corpus matrix
marks the repro as drift. Retirement is by re-seal: update the repro or
re-seal it against current behavior, with evidence. Removal without a
re-seal is not retirement; the mark stays a live candidate until a
re-seal lands.

## Why this holds

The same drift candidate recurred across successive reflection passes;
the recurrence was the signal, not noise. The retirement season's win was
the re-seal: the repro passes on current behavior with the moved
assumption updated, and the matrix runs green.

The end state to copy: reflection reads a fresh matrix every pass, a
FAIL/DRIFT row arms a candidate first, all-green prints a plain finding,
and an absent matrix changes nothing byte-for-byte.

## How to apply

- Refresh the matrix before reflection reads it; a stale matrix is a
  stale mirror.
- A drift mark carries: the repro, what moved, the observed behavior, and
  the WIN band (updated or re-sealed).
- The same candidate recurring across passes is the signal; repair the
  underlying assumption, never the signal.
""",
    ),
)


def _distill_corpus(root: Path) -> str:
    """The ratified-record corpus the distill scans: DESIGN.md plus the
    .rumpun/ledger/*.md akar records. A root without them yields an empty
    corpus and plugin_distill refuses (no proven gates, no pack)."""
    root = Path(root)
    chunks: list[str] = []
    design = root / "DESIGN.md"
    if design.is_file():
        chunks.append(design.read_text(encoding="utf-8", errors="replace"))
    ledger = root / scaffold.RUMPUN_DIR / "ledger"
    if ledger.is_dir():
        for path in sorted(ledger.glob("*.md")):
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def plugin_distill(root: Path, pack_name: str, source_note: str) -> dict[str, Any]:
    """Draft a pack of generalized priors from the campaign's proven gates.

    Scans the campaign's ratified records (DESIGN.md plus the .rumpun/ledger/
    akar records) for evidence that each known gate class is ratified here:
    the falsify enforcement, the band-mask guard, the stall-resume pattern,
    and the DRIFT retirement (DISTILLED_PRIORS). Each evidenced gate lands as
    priors/<key>.md — a fixed, generalized text hand-distilled from the
    ratified records; the scan only selects gates, so the output carries no
    season identifiers, campaign names, or paths by construction.

    The pack schema is drafted at 0.1.0 with the digest sealed over the
    emitted priors/ tree (priors_digest), a private vocabulary carrying
    exactly the campaign-agnostic season-identifier token class ("sid" —
    the strict v1 schema demands a non-empty vocabulary, and the
    season-identifier convention is the one term class that is private in
    every campaign while being no campaign's name), and the caller's
    provenance note verbatim as source.

    The draft lands at <root>/.rumpun/plugins/<name>-draft/ (beside installed
    packs, marked -draft for review; plugin_install is the promotion path and
    re-gates everything: digest verify, lint gate, priors-only copy).
    plugin_distill self-lints the staged pack before the atomic replace and
    refuses to emit a draft that fails the publish guardrails. Re-running
    replaces the previous draft. Never mutates the source records.

    Returns {"name", "pack", "priors", "skipped", "digest"}; raises
    PluginError on a bad name, an empty source note, no evidenced gates, or
    guardrail errors in the distill's own output.
    """
    root = Path(root)
    if not isinstance(pack_name, str) or not NAME_RE.match(pack_name):
        msg = f"pack name {pack_name!r} must match ^[a-z0-9][a-z0-9_-]*$"
        raise PluginError(msg)
    if not isinstance(source_note, str) or not source_note.strip():
        msg = "source note must be a non-empty provenance string"
        raise PluginError(msg)

    corpus = _distill_corpus(root)
    evidenced: list[DistilledPrior] = []
    skipped: list[str] = []
    for prior in DISTILLED_PRIORS:
        if any(pattern.search(corpus) for pattern in prior.evidence):
            evidenced.append(prior)
        else:
            skipped.append(prior.key)
    if not evidenced:
        msg = (
            f"{root}: no proven gates evidenced in the ratified records "
            f"({scaffold.RUMPUN_DIR}/ledger, DESIGN.md); a distill without "
            "proven gates is not a pack"
        )
        raise PluginError(msg)

    dest_root = plugins_dir(root)
    dest_root.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(dir=dest_root, prefix=f".{pack_name}-draft.staging-")
    )
    try:
        priors_dir = staging / PRIORS_DIRNAME
        priors_dir.mkdir()
        for prior in evidenced:
            target = priors_dir / f"{prior.key}.md"
            target.write_text(prior.body.strip() + "\n", encoding="utf-8")
        digest = priors_digest(staging)
        manifest = {
            "name": pack_name,
            "version": "0.1.0",  # a draft seals at 0.1.0; promotion bumps it
            "digest": digest,
            "private_vocabulary": ["sid"],
            "source": source_note.strip(),
        }
        manifest_path = staging / MANIFEST_NAME
        manifest_path.write_text(
            yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        findings = plugin_lint(staging, manifest)
        errors = [f for f in findings if f.severity == "error"]
        for finding in errors:
            logger.error("plugin distill: %s", finding.message)
        if errors:
            msg = (
                f"distill for {pack_name!r} refused: {len(errors)} guardrail "
                "error(s) in its own output; see the logged findings"
            )
            raise PluginError(msg)
        dest = dest_root / f"{pack_name}-draft"
        if dest.exists():
            shutil.rmtree(dest)
        os.replace(staging, dest)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    for prior in evidenced:
        logger.info("distilled prior: %s", f"priors/{prior.key}.md")
    for key in skipped:
        logger.info("gate not evidenced in the ratified records, skipped: %s", key)
    logger.info("draft pack sealed: %s (digest %s)", dest, digest)
    return {
        "name": pack_name,
        "pack": str(dest),
        "priors": [f"priors/{prior.key}.md" for prior in evidenced],
        "skipped": skipped,
        "digest": digest,
    }
