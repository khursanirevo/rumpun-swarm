"""s50 w2 pins — plugin distill: the flywheel's export (spec-first, red today).

The s50 band (musim/s50.yaml primary_change.expected_band): WIN when
"plugin distill emits a kaggle-base pack draft with priors/ content
extracted from the campaign's proven gates (the falsify gate, the
band-mask guard, the stall-resume pattern, the DRIFT retirement) AND the
manifest carries the computed digest AND plugin lint passes on the
emitted pack AND init --plugin scaffolds from it (repro) AND the suite is
green (188+ tests)"; LOSS otherwise.

Spec sources: musim/s50.yaml (the band), akar records audit-38 +
s44-harvest, the w1 declared CLI (`rumpun plugin distill <pack_name>
--source <note>`), and the landed s44 pack format + s46 install
machinery in rumpun/plugin.py. Spec, interface declarations, and the
measured red set: .rumpun/runs/s50/w2/notes.md.

Grafting: land this file in tests/ as-is (additions-only; existing suite
files stay untouched and the pre-existing suite stays green). Helpers
carry the _s50w2_ prefix so nothing collides with existing defs.

Pinned interface (declared for w1; reconcile at graft, as in s46):
- CLI verb: `rumpun plugin distill <pack_name> --source <note>` runs from
  a campaign root, exits 0, and writes the reviewable draft pack to
  .rumpun/plugins/<pack_name>-draft/ (manifest.yaml plus priors/).
- The draft manifest: name == <pack_name>, version "0.1.0", digest ==
  the computed sha256 over the draft's priors/ tree (sorted pack-relative
  posix rel path + b"\\0" + file bytes — the s46w2 pinned convention,
  landed as plugin.priors_digest), a schema-valid non-empty
  private_vocabulary, source == the note.
- plugin.plugin_lint(draft, manifest) reports zero error findings on the
  emitted pack. The w1 brief's "private_vocabulary: []" fails the landed
  lint schema, which requires a non-empty list; the distill must emit a
  lint-clean manifest (notes.md records this spec tension).
- Leak classes banned from priors/ (filenames and content): sid tokens
  (plugin.SID_TOKEN_RE), absolute-path tokens (plugin.ABS_PATH_RE /
  plugin.WIN_PATH_RE), and the campaign name token "rumpun" (the
  campaign carries no name field; the root dir name is its name).

The pins run the distill via subprocess (120s bound). A module-scoped
fixture builds a synthetic campaign — scaffolded via `rumpun init`, then
overlaid with this campaign's rumpun.yaml, season yamls, ledger records,
DESIGN.md, and GLOSSARY.md, the material the distill's scan reads — and
distills once; every pin consumes that one run. Writes stay in the
fixture's tmp tree; the source campaign is never mutated.

cli.main exits: argparse rejects the missing verb with SystemExit(2)
today (rc 2 in the subprocess), so every pin fails on its rc or file
assertion, not on an escaping exception.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from rumpun import plugin

S50W2_PACK_NAME = "kaggle-base"
S50W2_SOURCE_NOTE = "distilled from a 50-season campaign"
S50W2_TIMEOUT = 120
S50W2_GATE_STEMS = ("falsif", "band", "stall", "drift")
S50W2_NAME_RE = re.compile(r"\brumpun\b", re.IGNORECASE)


def _s50w2_repo() -> Path:
    """The repo root: the first pyproject.toml walking up from this file."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s50w2_env() -> dict[str, str]:
    """The subprocess env with the repo's src/ prepended to PYTHONPATH."""
    env = dict(os.environ)
    src = str(_s50w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s50w2_run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """One `python -m rumpun <argv>` subprocess from cwd, 120s bounded."""
    try:
        return subprocess.run(
            [sys.executable, "-m", "rumpun", *argv],
            cwd=str(cwd),
            env=_s50w2_env(),
            capture_output=True,
            text=True,
            timeout=S50W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(f"rumpun {' '.join(argv)} exceeded {S50W2_TIMEOUT}s") from exc


def _s50w2_priors_digest(pack: Path) -> str:
    """The declared v1 digest: sha256 over sorted priors/ (rel, NUL, bytes)."""
    digest = hashlib.sha256()
    priors = pack / "priors"
    for path in sorted(p for p in priors.rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _s50w2_priors_texts(pack: Path) -> list[tuple[str, str]]:
    """(rel posix path, text) for every file under pack/priors/, sorted."""
    priors = pack / "priors"
    out: list[tuple[str, str]] = []
    for path in sorted(priors.rglob("*")):
        if path.is_file():
            rel = path.relative_to(pack).as_posix()
            out.append((rel, path.read_text(encoding="utf-8", errors="replace")))
    return out


def _s50w2_manifest(draft: Path) -> dict[str, Any]:
    """The draft's manifest, strictly loaded; a legible red when unloadable."""
    try:
        return plugin.load_manifest(draft)
    except plugin.PluginError as exc:
        pytest.fail(f"{draft}: manifest does not load: {exc}")


def _s50w2_gate_campaign(tmp: Path) -> Path:
    """A scaffolded campaign overlaid with this campaign's gate material.

    The synthetic campaign carries the real rumpun.yaml, the season yamls,
    the ledger records, DESIGN.md, and GLOSSARY.md — the distill's scan
    surface — without mutating the source campaign.
    """
    repo = _s50w2_repo()
    campaign = tmp / "campaign"
    proc = _s50w2_run(tmp, ["init", str(campaign)])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    dot = campaign / ".rumpun"
    shutil.copytree(repo / ".rumpun" / "seasons", dot / "seasons", dirs_exist_ok=True)
    shutil.copytree(repo / ".rumpun" / "ledger", dot / "ledger", dirs_exist_ok=True)
    for name in ("DESIGN.md", "GLOSSARY.md"):
        shutil.copy2(repo / name, campaign / name)
    shutil.copy2(repo / ".rumpun" / "rumpun.yaml", dot / "rumpun.yaml")
    return campaign


@pytest.fixture(scope="module")
def s50w2_distill(tmp_path_factory: pytest.TempPathFactory) -> SimpleNamespace:
    """One distill run: the synthetic campaign builds once, distills once."""
    tmp = tmp_path_factory.mktemp("s50w2")
    campaign = _s50w2_gate_campaign(tmp)
    proc = _s50w2_run(
        campaign,
        ["plugin", "distill", S50W2_PACK_NAME, "--source", S50W2_SOURCE_NOTE],
    )
    draft = campaign / ".rumpun" / "plugins" / f"{S50W2_PACK_NAME}-draft"
    return SimpleNamespace(proc=proc, campaign=campaign, draft=draft)


# --- pin 1: the distill emits a lint-clean pack with the computed digest -----

def test_s50w2_distill_emits_lint_clean_pack(s50w2_distill: SimpleNamespace) -> None:
    """s50 pin 1 (red today: no `plugin distill` verb exists): the pack emits.

    Band clauses covered here: the kaggle-base draft exists with priors/
    content extracted from the proven gates (the four gate stems present),
    the manifest carries the computed digest (independently recomputed and
    cross-checked against plugin.priors_digest), and plugin lint reports
    zero errors on the emitted pack.
    """
    proc = s50w2_distill.proc
    draft = s50w2_distill.draft
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert draft.is_dir(), str(draft)
    manifest = _s50w2_manifest(draft)
    assert manifest.get("name") == S50W2_PACK_NAME, manifest
    assert manifest.get("version") == "0.1.0", manifest
    digest = manifest.get("digest")
    assert isinstance(digest, str) and plugin.DIGEST_RE.match(digest), digest
    computed = _s50w2_priors_digest(draft)
    assert digest == computed, (digest, computed)
    assert plugin.priors_digest(draft) == computed, (plugin.priors_digest(draft), computed)
    vocab = manifest.get("private_vocabulary")
    assert isinstance(vocab, list) and vocab, manifest
    assert all(isinstance(term, str) and plugin.TERM_RE.match(term) for term in vocab), vocab
    assert manifest.get("source") == S50W2_SOURCE_NOTE, manifest
    texts = _s50w2_priors_texts(draft)
    assert len(texts) >= 1, "the distill emitted no priors/ content"
    combined = "\n".join(text for _, text in texts).lower()
    missing = [stem for stem in S50W2_GATE_STEMS if stem not in combined]
    assert missing == [], f"gate stems absent from the distilled priors: {missing}"
    findings = plugin.plugin_lint(draft, manifest)
    errors = [finding.message for finding in findings if finding.severity == "error"]
    assert errors == [], errors


# --- pin 2: the distilled priors carry no campaign privates ------------------

def test_s50w2_distilled_priors_carry_no_campaign_privates(
    s50w2_distill: SimpleNamespace,
) -> None:
    """s50 pin 2 (red today: the distill never runs): no sids, paths, names.

    The guardrails lint's own rules applied to the distill's output: no
    sid token, no absolute-path token, and no campaign name token may
    appear in any priors/ filename or content line, and the emitted pack
    lints clean under the manifest's own private_vocabulary.
    """
    proc = s50w2_distill.proc
    draft = s50w2_distill.draft
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert draft.is_dir(), str(draft)
    manifest = _s50w2_manifest(draft)
    texts = _s50w2_priors_texts(draft)
    assert texts, "the distill emitted no priors/ content"
    for rel, text in texts:
        label = f"{rel}: {text[:200]!r}"
        sid = plugin.SID_TOKEN_RE.search(text)
        assert sid is None, f"{rel}: sid token leaked into priors: {label}"
        for pattern in (plugin.ABS_PATH_RE, plugin.WIN_PATH_RE):
            hit = pattern.search(text)
            assert hit is None, f"{rel}: absolute-path token leaked: {label}"
        name_hit = S50W2_NAME_RE.search(text)
        assert name_hit is None, f"{rel}: campaign name token leaked: {label}"
    for path in sorted((draft / "priors").rglob("*")):
        rel = path.relative_to(draft).as_posix()
        sid = plugin.SID_TOKEN_RE.search(rel)
        assert sid is None, f"{rel}: sid token in a priors filename"
        name_hit = S50W2_NAME_RE.search(rel)
        assert name_hit is None, f"{rel}: campaign name in a priors filename"
    findings = plugin.plugin_lint(draft, manifest)
    errors = [finding.message for finding in findings if finding.severity == "error"]
    assert errors == [], errors


# --- pin 3: the round trip: distill -> install -> the pack lands -------------

def test_s50w2_install_round_trip_lands_the_pack(s50w2_distill: SimpleNamespace) -> None:
    """s50 pin 3 (red today: no draft to install): the distill-installs round trip.

    `rumpun plugin install` on the emitted draft exits 0, the campaign's
    plugins dir holds the pack (manifest.yaml plus the same priors/ tree),
    and the plugins.yml registry records the pack name with the pack
    digest. The s50 band's init --plugin clause rides the same
    plugin_install gate; this pin holds the install step itself.
    """
    proc = s50w2_distill.proc
    campaign = s50w2_distill.campaign
    draft = s50w2_distill.draft
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert draft.is_dir(), str(draft)
    install = _s50w2_run(campaign, ["plugin", "install", str(draft)])
    assert install.returncode == 0, install.stdout + install.stderr
    installed = campaign / ".rumpun" / "plugins" / S50W2_PACK_NAME
    assert (installed / "manifest.yaml").is_file(), str(installed)
    draft_rels = {rel for rel, _ in _s50w2_priors_texts(draft)}
    installed_rels = {rel for rel, _ in _s50w2_priors_texts(installed)}
    assert installed_rels == draft_rels, (sorted(draft_rels), sorted(installed_rels))
    records = {record["name"]: record for record in plugin.plugin_list(campaign)}
    assert S50W2_PACK_NAME in records, sorted(records)
    assert records[S50W2_PACK_NAME]["digest"] == _s50w2_priors_digest(draft)
    installed_manifest = _s50w2_manifest(installed)
    assert installed_manifest["digest"] == _s50w2_priors_digest(installed)
