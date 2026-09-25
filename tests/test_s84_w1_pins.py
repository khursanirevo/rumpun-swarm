"""s84 w1 pins — the audit reads its own resolution trail (issue #6).

Spec sources: .rumpun/runs/s84/w1/prompt.md; issue #6
(khursanirevo/rumpun#6): audit-44 re-emitted audit-43's three
usefulness-decade-1 residuals verbatim the same day s80 resolved all
three (issues #3/#4 closed on fresh measurement, #5 scoped into the
repro-backed-closure standard). Precedents: the s35 run_audit pins in
tests/test_rumpun.py (the audit fixture campaign, hand-built usefulness
records), the s80 w2 pins (the fixture harvest through
akar.append_record).

Offline: these pins make no gh call -- the resolution trail is fixture
rows ({number, state, body}) passed straight to run_audit's issue_trail
parameter, mirroring the real board's citation shape: an issue cites a
candidate by quoting its line minus the `candidate: ` prefix, and the
harvest record names the issue number in its implies line.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from rumpun import akar, audit

logger = logging.getLogger(__name__)

RESIDUAL_ID = "usefulness-decade-1"

# The three real usefulness-decade-1 residuals audit-43 armed and audit-44
# re-armed verbatim, verbatim from the ledger record, plus one fresh
# residual no issue ever cited (the passthrough case).
T1 = (
    "Reported locking repairs, citation checks, regression tooling, and "
    "reduced rendering provide specific utility. Independent artifact checks "
    "remain absent here."
)
T2 = (
    "The ledger establishes 24 WIN, eight LOSS, and two missing verdicts, "
    "not 34 completed improvements."
)
T3 = (
    "Recorded verdicts establish what evaluators wrote. They do not "
    "independently establish implementation correctness or practical value."
)
T4 = (
    "No external workload or operator outcome demonstrates usefulness beyond "
    "maintaining rumpun itself."
)


def _emitted(text: str) -> str:
    """The candidate's emitted text: the line minus the `candidate: ` prefix."""
    return f"usefulness residual: {text} ({RESIDUAL_ID})"


S9_HARVEST_BODY = (
    "season s9: completed\n"
    "\n"
    "verdict: WIN\n"
    "implies: the deep residual #5 became a standing standard - the "
    "repro-backed-closure contract in the pack, pinned and commented on the "
    "issue, which stays open by design\n"
)


def _issue_row(number: int, state: str, text: str) -> dict[str, object]:
    """One fixture trail row mirroring the real issues' citation shape."""
    return {
        "number": number,
        "state": state,
        "body": (
            "> " + _emitted(text) + "\n\nSource: audit-43 (2026-09-17), "
            "`.rumpun/ledger/2026-09-17_audit-43.md`, `candidate:` line."
        ),
    }


def _residual_record(residuals: list[str]) -> str:
    """A hand-built usefulness-decade-1 record (read paths never seal-check)."""
    bullets = "\n".join(f"- {text}" for text in residuals)
    return (
        "# akar record: usefulness-decade-1\n"
        "id: usefulness-decade-1\n"
        "date: 2026-09-15\n"
        "title: PARTIALLY USEFUL (decade 1 review)\n"
        "verdict: PARTIALLY USEFUL\n"
        "residuals:\n"
        f"{bullets}\n"
        "sha256: " + "0" * 64 + "\n"
    )


def _campaign(tmp_path: Path, residuals: list[str]) -> Path:
    """Minimal audit campaign: one engine season, the fixture decade record.

    Layout mirrors the real campaign: <tmp>/s84w1proj/DESIGN-free, root at
    <tmp>/s84w1proj/.rumpun with rumpun.yaml, seasons/s1.yaml, runs/s1/,
    and ledger/usefulness-decade-1.md.
    """
    campaign = tmp_path / "s84w1proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text("autonomy:\n  stage: manual\n", encoding="utf-8")
    (root / "seasons" / "s1.yaml").write_text(
        "id: s1\nparent: s0\ngoal: fixture season for the s84 w1 pins\n",
        encoding="utf-8",
    )
    (root / "runs" / "s1").mkdir()
    (root / "ledger" / f"{RESIDUAL_ID}.md").write_text(
        _residual_record(residuals), encoding="utf-8"
    )
    return root


def _run_audit(root: Path, **kwargs: object) -> Path:
    """run_audit with the issue_trail seam; a TypeError names the spec.

    Pre-landing, the seam's absence is the spec-reason red: issue #6 asks
    for a trail-reading composer, so a run_audit without the seam cannot
    even express the fixture.
    """
    try:
        return audit.run_audit(root, **kwargs)
    except TypeError as exc:
        pytest.fail(f"issue_trail seam unlanded in run_audit (issue #6): {exc}")


def _trail() -> list[dict[str, object]]:
    """The real board's shape: #3/#4 CLOSED, #5 OPEN (stays open by design)."""
    return [
        _issue_row(3, "CLOSED", T1),
        _issue_row(4, "CLOSED", T2),
        _issue_row(5, "OPEN", T3),
    ]


def _lines(text: str, prefix: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith(prefix)]


def test_s84w1_resolved_candidates_suppressed(tmp_path):
    """Pin 1: resolved candidates do not re-emit as candidates.

    The full real situation in miniature: T1/T2 cited by CLOSED issues
    (the closed-issue leg), T3 cited by an OPEN issue whose resolution
    the s9-harvest implies line names (the named-resolution leg), and
    the fresh T4 uncited anywhere. T1-T3 come back as `resolved: ` lines
    carrying their evidence; only T4 stays a candidate.
    """
    root = _campaign(tmp_path, [T1, T2, T3, T4])
    akar.append_record(root, "s9-harvest", "season s9 harvest", S9_HARVEST_BODY)
    text = _run_audit(root, issue_trail=_trail()).read_text(encoding="utf-8")
    cands = _lines(text, "candidate: ")
    assert cands == [f"candidate: {_emitted(T4)}"], (
        f"resolved candidates re-emitted: {cands}"
    )
    resolved = _lines(text, "resolved: ")
    assert resolved == [
        f"resolved: {_emitted(T1)} — issue #3 closed",
        f"resolved: {_emitted(T2)} — issue #4 closed",
        f"resolved: {_emitted(T3)} — issue #5 named in s9-harvest",
    ], f"resolved markers wrong: {resolved}"


def test_s84w1_unresolved_passthrough(tmp_path):
    """Pin 2: a fresh candidate with no resolution trail still emits.

    An empty trail (consulted, nothing cites it) leaves the fresh
    residual a live candidate citing its record -- the audit never
    suppresses on a guess.
    """
    root = _campaign(tmp_path, [T4])
    text = _run_audit(root, issue_trail=[]).read_text(encoding="utf-8")
    assert f"candidate: {_emitted(T4)}" in text.splitlines()


def test_s84w1_resolved_marker_excluded_from_feed(tmp_path):
    """Pin 3: the marker choice is `resolved: `, and the feed never sees it.

    candidate_lines() (the verb's output, the kanban backlog's source)
    keeps only `candidate: ` lines, so a resolved candidate cannot
    re-enter the backlog or re-file to the board. The record body keeps
    the evidence-bearing markers.
    """
    root = _campaign(tmp_path, [T1, T2, T3, T4])
    akar.append_record(root, "s9-harvest", "season s9 harvest", S9_HARVEST_BODY)
    record = _run_audit(root, issue_trail=_trail())
    text = record.read_text(encoding="utf-8")
    assert audit.candidate_lines(record) == [f"candidate: {_emitted(T4)}"]
    resolved = _lines(text, "resolved: ")
    assert len(resolved) == 3, f"expected three resolved markers: {resolved}"
    assert all(
        line.startswith("resolved: usefulness residual: ") for line in resolved
    ), f"markers lost the emitted-text shape: {resolved}"
    assert (
        f"resolved: {_emitted(T3)} — issue #5 named in s9-harvest" in resolved
    ), f"the named-resolution marker is missing: {resolved}"


def test_s84w1_no_trail_keeps_candidates(tmp_path):
    """Pin 4: without a trail the composer is byte-stable with s84-w0.

    No issue_trail argument means no board evidence was consulted: every
    residual stays a live candidate, no resolved markers appear, and the
    pre-existing emission shape holds for the standing suite.
    """
    root = _campaign(tmp_path, [T1, T2, T3])
    text = _run_audit(root).read_text(encoding="utf-8")
    assert f"candidate: {_emitted(T1)}" in text.splitlines()
    assert f"candidate: {_emitted(T2)}" in text.splitlines()
    assert f"candidate: {_emitted(T3)}" in text.splitlines()
    assert "resolved: " not in text
