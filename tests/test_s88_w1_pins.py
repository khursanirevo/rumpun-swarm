"""s88 w1 pins — the verdict-vs-correctness prior's checkable surface.

Spec sources: .rumpun/runs/s88/w1/prompt.md; issue #5
(khursanirevo/rumpun#5, the audit-43 epistemics residual -- it stays
OPEN as the standing standard); the sibling contract at
.rumpun/plugins/kancil-base-draft/priors/templates/
repro-backed-closure.md (s80 w2). Precedents: the s80 w2 pins (the
real-draft surface, the pack-digest-live seal), the s86 w2 pins (the
named-refusal / lint-clean discipline), the s51 w2 pins (plugin_lint
on a pack).

Offline: these pins make no gh call and no route call; they read the
real draft pack and its manifest only.

Contract these pins hold -- the draft pack seals the promoted
standard, and the prior draws the line the repro-backed closure sits
inside:

1. The kancil-base draft pack seals digest-verified
   (manifest digest == plugin.priors_digest) with BOTH standing
   priors present: repro-backed-closure.md (the s80 defect-shape
   contract) and verdict-vs-correctness.md (the s88 general line).
2. The draft pack lints clean (plugin.plugin_lint: zero findings) --
   the #10 defect class (a draft that cannot seal/install) stays out.
3. The prior names the sibling contract and the standing issue, and
   states the deliberately-open shape ("No season closes it").
4. The prior maps claim words to evidence classes: a verdict
   establishes the evaluator's band judgment; a repro establishes
   implementation correctness; an external task or a matched baseline
   establishes practical value; absent all three, the absence is
   stated by name.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rumpun import plugin

S88W1_REPO = Path(__file__).resolve().parents[1]
S88W1_DRAFT = S88W1_REPO / ".rumpun" / "plugins" / "kancil-base-draft"
S88W1_PRIOR = (
    S88W1_DRAFT / "priors" / "templates" / "verdict-vs-correctness.md"
)
S88W1_SIBLING = (
    S88W1_DRAFT / "priors" / "templates" / "repro-backed-closure.md"
)


def _s88w1_manifest() -> dict:
    """The draft pack's manifest, strictly loaded; a legible red when not."""
    try:
        return plugin.load_manifest(S88W1_DRAFT)
    except Exception as exc:
        pytest.fail(f"{S88W1_DRAFT}: manifest does not load: {exc}")


def _s88w1_prior_text(path: Path) -> str:
    """A prior template's text; a legible red when unreadable."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        pytest.fail(f"{path}: unreadable: {exc}")


def test_s88w1_draft_pack_seals_both_standing_priors() -> None:
    """The pack seal is live and both standing priors are present.

    The digest is probed live (plugin.priors_digest), never hardcoded:
    a prior added without re-sealing turns this pin red, and so does a
    sealed digest that no longer matches the tree.
    """
    manifest = _s88w1_manifest()
    declared = manifest.get("digest")
    computed = plugin.priors_digest(S88W1_DRAFT)
    assert isinstance(declared, str) and declared == computed, (
        declared,
        computed,
    )
    templates = sorted(
        p.name for p in (S88W1_DRAFT / "priors" / "templates").glob("*.md")
    )
    assert "verdict-vs-correctness.md" in templates, templates
    assert "repro-backed-closure.md" in templates, templates


def test_s88w1_draft_pack_lints_clean() -> None:
    """plugin_lint on the real draft reports zero findings.

    Errors are publish rejections (sids, absolute paths, private
    vocabulary, manifest violations): a promoted prior that trips the
    lint must not sit in the pack silently.
    """
    manifest = _s88w1_manifest()
    findings = plugin.plugin_lint(S88W1_DRAFT, manifest)
    assert not findings, [str(f) for f in findings]


def test_s88w1_prior_carries_the_line_and_the_sibling() -> None:
    """The prior names the sibling contract, the issue, and the shape.

    Text-level: the house sections stand, the sibling contract is
    cited by file, issue #5 is named as the standing standard's home,
    and the deliberately-open clause is present verbatim.
    """
    text = _s88w1_prior_text(S88W1_PRIOR)
    for section in ("## What it is", "## The skeleton", "## How to apply"):
        assert section in text, section
    collapsed = " ".join(text.split())
    assert "repro-backed-closure.md" in text, "sibling contract not cited"
    assert "Issue #5" in text, "the standing issue is not named"
    assert "deliberately" in text and "open" in text, "open shape unstated"
    assert "No season closes it" in collapsed, "the open clause is missing"


def test_s88w1_prior_maps_claims_to_evidence_classes() -> None:
    """The evidence-class line stands: verdict / repro / external task.

    The mapping the prior distills: a band verdict is not a repro is
    not a baseline. Each class is named; the absence clause names all
    three by their absence.
    """
    text = _s88w1_prior_text(S88W1_PRIOR)
    assert "does not establish" in text, "the line's negation is missing"
    assert "external task" in text, "the external-task class is missing"
    assert "matched baseline" in text, "the baseline class is missing"
    assert "no repro, no external task, no baseline" in text, (
        "the absence clause is missing"
    )
    assert "verdict: WIN" in text, "the verdict-class mapping is missing"
