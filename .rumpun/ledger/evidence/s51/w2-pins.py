"""s51 w2 pins — the extended distill: patterns and templates (spec-first, red today).

The s51 band (seasons/s51.yaml primary_change.expected_band): WIN if
"distill emits evidenced patterns and templates inside priors/
(priors/patterns/, priors/templates/), generalized (no sids, campaign
names, or absolute paths), self-lint clean, digest verified over the
full priors/ tree, install round-trip green, and the suite holds its
floor (the four known reds stay the only reds)"; LOSS otherwise.

Spec sources: seasons/s51.yaml (the band, the benih lane briefs, and the
baseline naming the campaign's four working patterns and four reusable
templates), akar records s50-harvest + audit-38, the landed s50 distill
in rumpun/plugin.py (plugin_distill, DISTILLED_PRIORS, plugin_lint,
priors_digest), and the s50 pins (tests/test_s50_w2_pins.py) as the
shape precedent. Spec, interface declarations, and the measured red
set: .rumpun/runs/s51/w2/notes.md.

Grafting: land this file in tests/ as-is (additions-only; existing
suite files stay untouched and the pre-existing suite stays at its
floor). Helpers carry the _s51w2_ prefix so nothing collides with
existing defs.

Pinned interface (declared for w1; reconcile at graft, as in s46/s50):
- CLI unchanged: `rumpun plugin distill <pack_name> --source <note>`
  (subprocess, 120s bound) exits 0 from a campaign root and writes the
  reviewable draft to .rumpun/plugins/<pack_name>-draft/ — now with the
  evidenced patterns at priors/patterns/<key>.md and reusable templates
  at priors/templates/<key>.md beside the s50 gates at priors/<key>.md.
- The extension is additive: the four s50 gate stems (falsif, band,
  stall, drift) stay present in the distilled priors.
- Selection is evidence-driven as in s50: a class lands only when the
  ratified records (DESIGN.md plus .rumpun/ledger/*.md) evidence it.
  The band names the campaign's four working patterns (spec-first
  pinning, merge reconciliation, harvest close, the replay corpus gate)
  and four templates (season yaml, harvest note, pins header, the akar
  record shape); the pins require the emitted classes to cover those
  stems, checked as case-folded substrings over each class's filenames
  and combined text.
- Generalization: no sid token (plugin.SID_TOKEN_RE), no absolute-path
  token (plugin.ABS_PATH_RE / plugin.WIN_PATH_RE), and no campaign name
  token ("rumpun" — the root dir name; the campaign carries no name
  field) in any patterns/ or templates/ filename or content line.
- Self-lint clean: plugin.plugin_lint on the emitted draft reports zero
  error findings; the manifest schema stays the unchanged s44 v1 schema
  (the lint rejects unknown keys, so a lint-clean manifest is the proof
  the schema is unchanged).
- Digest and round trip: the manifest digest verifies over the FULL
  priors/ tree (gates + patterns + templates) by independent sha256
  recomputation (sorted pack-relative posix rel path, NUL, file bytes —
  the s46w2 pinned convention, landed as plugin.priors_digest) and
  against plugin.priors_digest; `plugin install` on the draft installs
  the pack round-trip: plugins/<name>/ carries the draft's exact
  priors/ rel set including the new classes, and the plugins.yml
  registry row carries the pack digest.

The pins run the distill via subprocess (120s bound). A module-scoped
fixture builds a synthetic campaign — scaffolded via `rumpun init`,
then overlaid with this campaign's rumpun.yaml, season yamls, ledger
records, DESIGN.md, and GLOSSARY.md, the material the distill's scan
reads — and distills once; every pin consumes that one run. Writes stay
in the fixture's tmp tree; the source campaign is never mutated.

Today (main, pre-extension): the s50 distill exists and emits the four
gates only; priors/patterns/ and priors/templates/ are never created,
so every pin fails on the missing new classes — the intended spec
reason — not on an escaping exception.
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

S51W2_PACK_NAME = "kaggle-base"
S51W2_SOURCE_NOTE = "distilled from a 51-season campaign"
S51W2_TIMEOUT = 120
# The s50 gates (the extension is additive) and the s51 band's named
# pattern/template classes, as case-folded stems. Each group is any-of:
# a class counts as covered when any stem in its group appears.
S51W2_GATE_STEMS: tuple[str, ...] = ("falsif", "band", "stall", "drift")
S51W2_PATTERN_STEMS: tuple[tuple[str, ...], ...] = (
    ("spec",),  # spec-first pinning
    ("merge",),  # merge reconciliation
    ("harvest",),  # harvest close
    ("replay", "corpus"),  # the replay corpus gate
)
S51W2_TEMPLATE_STEMS: tuple[tuple[str, ...], ...] = (
    ("season",),  # season yaml
    ("harvest",),  # harvest note
    ("pin",),  # pins header
    ("akar", "record"),  # the akar record shape
)
S51W2_NAME_RE = re.compile(r"\brumpun\b", re.IGNORECASE)


def _s51w2_repo() -> Path:
    """The repo root: the first pyproject.toml walking up from this file."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s51w2_env() -> dict[str, str]:
    """The subprocess env with the repo's src/ prepended to PYTHONPATH."""
    env = dict(os.environ)
    src = str(_s51w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s51w2_run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """One `python -m rumpun <argv>` subprocess from cwd, 120s bounded."""
    try:
        return subprocess.run(
            [sys.executable, "-m", "rumpun", *argv],
            cwd=str(cwd),
            env=_s51w2_env(),
            capture_output=True,
            text=True,
            timeout=S51W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(f"rumpun {' '.join(argv)} exceeded {S51W2_TIMEOUT}s") from exc


def _s51w2_priors_digest(pack: Path) -> str:
    """The declared v1 digest: sha256 over sorted priors/ (rel, NUL, bytes)."""
    digest = hashlib.sha256()
    priors = pack / "priors"
    for path in sorted(p for p in priors.rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _s51w2_priors_texts(pack: Path) -> list[tuple[str, str]]:
    """(rel posix path, text) for every file under pack/priors/, sorted."""
    priors = pack / "priors"
    out: list[tuple[str, str]] = []
    for path in sorted(priors.rglob("*")):
        if path.is_file():
            rel = path.relative_to(pack).as_posix()
            out.append((rel, path.read_text(encoding="utf-8", errors="replace")))
    return out


def _s51w2_class_texts(pack: Path, cls: str) -> list[tuple[str, str]]:
    """The content class's (rel, text) files: under priors/<cls>/, or the
    gate class (top-level priors/ files only) when cls is empty."""
    base = pack / "priors" / cls if cls else pack / "priors"
    out: list[tuple[str, str]] = []
    if not base.is_dir():
        return out
    paths = sorted(base.rglob("*")) if cls else sorted(base.glob("*"))
    for path in paths:
        if path.is_file():
            rel = path.relative_to(pack).as_posix()
            out.append((rel, path.read_text(encoding="utf-8", errors="replace")))
    return out


def _s51w2_missing_stems(
    texts: list[tuple[str, str]], stems: tuple[tuple[str, ...], ...]
) -> list[str]:
    """Stem groups with no case-folded hit in the class's names and text."""
    combined = "\n".join(f"{rel}\n{text}" for rel, text in texts).lower()
    return ["/".join(group) for group in stems if not any(s in combined for s in group)]


def _s51w2_manifest(draft: Path) -> dict[str, Any]:
    """The draft's manifest, strictly loaded; a legible red when unloadable."""
    try:
        return plugin.load_manifest(draft)
    except plugin.PluginError as exc:
        pytest.fail(f"{draft}: manifest does not load: {exc}")


def _s51w2_gate_campaign(tmp: Path) -> Path:
    """A scaffolded campaign overlaid with this campaign's gate material.

    The synthetic campaign carries the real rumpun.yaml, the season
    yamls, the ledger records, DESIGN.md, and GLOSSARY.md — the
    distill's scan surface — without mutating the source campaign.
    """
    repo = _s51w2_repo()
    campaign = tmp / "campaign"
    proc = _s51w2_run(tmp, ["init", str(campaign)])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    dot = campaign / ".rumpun"
    shutil.copytree(repo / ".rumpun" / "seasons", dot / "seasons", dirs_exist_ok=True)
    shutil.copytree(repo / ".rumpun" / "ledger", dot / "ledger", dirs_exist_ok=True)
    for name in ("DESIGN.md", "GLOSSARY.md"):
        shutil.copy2(repo / name, campaign / name)
    shutil.copy2(repo / ".rumpun" / "rumpun.yaml", dot / "rumpun.yaml")
    return campaign


@pytest.fixture(scope="module")
def s51w2_distill(tmp_path_factory: pytest.TempPathFactory) -> SimpleNamespace:
    """One distill run: the synthetic campaign builds once, distills once."""
    tmp = tmp_path_factory.mktemp("s51w2")
    campaign = _s51w2_gate_campaign(tmp)
    proc = _s51w2_run(
        campaign,
        ["plugin", "distill", S51W2_PACK_NAME, "--source", S51W2_SOURCE_NOTE],
    )
    draft = campaign / ".rumpun" / "plugins" / f"{S51W2_PACK_NAME}-draft"
    return SimpleNamespace(proc=proc, campaign=campaign, draft=draft)


# --- pin 1: the distill emits the new classes, gates intact, self-lint clean --

def test_s51w2_distill_emits_patterns_and_templates(s51w2_distill: SimpleNamespace) -> None:
    """s51 pin 1 (red today: the distill emits gates only): the classes emit.

    Band clauses here: the distill emits evidenced patterns and templates
    inside priors/ (priors/patterns/ and priors/templates/ non-empty and
    covering the band's named classes), the extension is additive (the
    s50 gate stems stay in priors/), and the emitted pack is self-lint
    clean (plugin_lint zero errors, unchanged s44 manifest schema).
    """
    proc = s51w2_distill.proc
    draft = s51w2_distill.draft
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert draft.is_dir(), str(draft)
    manifest = _s51w2_manifest(draft)
    assert manifest.get("name") == S51W2_PACK_NAME, manifest
    assert manifest.get("version") == "0.1.0", manifest
    assert isinstance(manifest.get("digest"), str), manifest
    gates = _s51w2_class_texts(draft, "")
    assert gates, "the distill emitted no gate priors"
    missing_gates = _s51w2_missing_stems(gates, tuple((s,) for s in S51W2_GATE_STEMS))
    assert missing_gates == [], f"gate stems absent from the distilled priors: {missing_gates}"
    patterns = _s51w2_class_texts(draft, "patterns")
    templates = _s51w2_class_texts(draft, "templates")
    assert patterns, "no priors/patterns/ content: the extension is missing"
    assert templates, "no priors/templates/ content: the extension is missing"
    missing_p = _s51w2_missing_stems(patterns, S51W2_PATTERN_STEMS)
    assert missing_p == [], f"pattern stems absent from priors/patterns/: {missing_p}"
    missing_t = _s51w2_missing_stems(templates, S51W2_TEMPLATE_STEMS)
    assert missing_t == [], f"template stems absent from priors/templates/: {missing_t}"
    findings = plugin.plugin_lint(draft, manifest)
    errors = [finding.message for finding in findings if finding.severity == "error"]
    assert errors == [], errors


# --- pin 2: the new classes carry no campaign privates ------------------------

def test_s51w2_new_classes_carry_no_campaign_privates(
    s51w2_distill: SimpleNamespace,
) -> None:
    """s51 pin 2 (red today: the classes never emit): no sids, paths, names.

    The s50 pin-2 shape applied to the new classes: no sid token, no
    absolute-path token, and no campaign name token in any patterns/ or
    templates/ filename or content line.
    """
    proc = s51w2_distill.proc
    draft = s51w2_distill.draft
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert draft.is_dir(), str(draft)
    patterns = _s51w2_class_texts(draft, "patterns")
    templates = _s51w2_class_texts(draft, "templates")
    assert patterns, "no priors/patterns/ content: the extension is missing"
    assert templates, "no priors/templates/ content: the extension is missing"
    for rel, text in [*patterns, *templates]:
        label = f"{rel}: {text[:200]!r}"
        hit = plugin.SID_TOKEN_RE.search(rel)
        assert hit is None, f"{rel}: sid token in a new-class filename"
        hit = S51W2_NAME_RE.search(rel)
        assert hit is None, f"{rel}: campaign name in a new-class filename"
        hit = plugin.SID_TOKEN_RE.search(text)
        assert hit is None, f"{rel}: sid token leaked into the new classes: {label}"
        for path_re in (plugin.ABS_PATH_RE, plugin.WIN_PATH_RE):
            hit = path_re.search(text)
            assert hit is None, f"{rel}: absolute-path token leaked: {label}"
        hit = S51W2_NAME_RE.search(text)
        assert hit is None, f"{rel}: campaign name token leaked: {label}"


# --- pin 3: full-tree digest and the install round trip -----------------------

def test_s51w2_full_tree_digest_and_install_round_trip(
    s51w2_distill: SimpleNamespace,
) -> None:
    """s51 pin 3 (red today: no new classes in the tree): digest + round trip.

    The manifest digest verifies over the FULL priors/ tree (gates +
    patterns + templates) by independent recomputation and against
    plugin.priors_digest, and `plugin install` on the draft installs the
    pack round-trip: plugins/kaggle-base/ carries the draft's exact
    priors/ rel set including the new classes, and the plugins.yml
    registry records the pack with that digest.
    """
    proc = s51w2_distill.proc
    campaign = s51w2_distill.campaign
    draft = s51w2_distill.draft
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert draft.is_dir(), str(draft)
    manifest = _s51w2_manifest(draft)
    digest = manifest.get("digest")
    computed = _s51w2_priors_digest(draft)
    assert isinstance(digest, str) and digest == computed, (digest, computed)
    live = plugin.priors_digest(draft)
    assert live == computed, (live, computed)
    patterns = _s51w2_class_texts(draft, "patterns")
    templates = _s51w2_class_texts(draft, "templates")
    assert patterns, "no priors/patterns/ content: the extension is missing"
    assert templates, "no priors/templates/ content: the extension is missing"
    install = _s51w2_run(campaign, ["plugin", "install", str(draft)])
    assert install.returncode == 0, install.stdout + install.stderr
    installed = campaign / ".rumpun" / "plugins" / S51W2_PACK_NAME
    assert (installed / "manifest.yaml").is_file(), str(installed)
    draft_rels = {rel for rel, _ in _s51w2_priors_texts(draft)}
    installed_rels = {rel for rel, _ in _s51w2_priors_texts(installed)}
    assert installed_rels == draft_rels, (sorted(draft_rels), sorted(installed_rels))
    assert any(rel.startswith("priors/patterns/") for rel in installed_rels), (
        "patterns/ did not install",
        sorted(installed_rels),
    )
    assert any(rel.startswith("priors/templates/") for rel in installed_rels), (
        "templates/ did not install",
        sorted(installed_rels),
    )
    records = {record["name"]: record for record in plugin.plugin_list(campaign)}
    assert S51W2_PACK_NAME in records, sorted(records)
    assert records[S51W2_PACK_NAME]["digest"] == computed, records[S51W2_PACK_NAME]
    installed_manifest = _s51w2_manifest(installed)
    assert installed_manifest["digest"] == _s51w2_priors_digest(installed)
