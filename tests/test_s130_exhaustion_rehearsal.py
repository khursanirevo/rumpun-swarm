"""s130 w1 pins -- the honest exit rehearsed before it is needed.

Spec source: the s130 w1 brief (.rumpun/runs/s130/w1/prompt.md) and the
seam contracts in src/rumpun/audit.py (seal_usefulness_assessment /
usefulness_inputs / read_usefulness_assessment) and src/rumpun/evolve.py
(_assessment_due, the hint behind `rumpun evolve plan`). The assessment
module's verdict takes CONTINUE | PAUSE | EXHAUSTED, and the campaign has
only ever sealed CONTINUE; the stop path should work the day it is
needed, so these pins rehearse it in tmp campaigns:

1. Seal + round-trip: an EXHAUSTED assessment seals through
   audit.seal_usefulness_assessment with zero fronts and the satisfied
   lines; the body keeps every section header (byte-stable at every
   arity) and read_usefulness_assessment reads it back field-identical
   (id, title, verdict, the default basis line, weight, fronts,
   satisfied, epics).
2. Pre-flight: usefulness_inputs passes an EXHAUSTED mapping with empty
   fronts through to the seal unchanged -- verdict, empty fronts,
   satisfied lines, basis None (the default rides the seal).
3. Plan surface: with usefulness-<parent> sealed EXHAUSTED, the planner's
   drought hint stays silent -- the campaign is not asked to continue --
   and the draft still lands (the hint never blocks).
4. Contrast guard: a verdict-bearing CONTINUE seal behind a full drought
   still announces and names the seal -- the silence is the exhausted
   state, not a broken hint.

Offline: in-process over tmp_path fixture campaigns; the seals land
through akar.append_record (the audit seal calls it) in the tmp ledger
only -- the real campaign ledger is never written, and no season runs.

Red-first honesty: the contract holds on the current tree, so the pins
land green on arrival; the red proof ran against scratch trees under
/tmp (never the shared tree; a sibling lane works in parallel). Dropping
EXHAUSTED from USEFULNESS_VERDICTS turned pin1, pin2, and pin3 red with
the vocabulary ValueError (pin4's CONTINUE seal stayed green), and a
drought walk that skips EXHAUSTED seals -- the campaign asked to
continue -- turned pin3 red with the due announcement. Both mutations
were observed red before this file landed.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from rumpun import audit, evolve

# The default basis line, pinned verbatim: the EXHAUSTED body must carry
# the same line the s88 contract pinned for CONTINUE.
_S130_DEFAULT_BASIS = (
    "directive seq 9 - usefulness exhaustion is the stopping criterion;"
    " every front below names its owner and next-action"
)
_S130_TITLE = "the per-season usefulness assessment over the whole ledger"
_S130_SATISFIED = [
    "exhaustion is the stopping criterion, answered honestly",
    "the ledger stands as the campaign record",
]
_S130_FRONT = {
    "name": "close the campaign",
    "owner": "operator",
    "basis": "the ledger is whole",
    "next": "archive the ledger",
}
_S130_CHAIN = [
    ("s113", "s112"),
    ("s112", "s111"),
    ("s111", "s110"),
    ("s110", "s109"),
    ("s109", "s108"),
    ("s108", "s107"),
]


def _s130_season_text(sid: str, parent_id: str | None) -> str:
    """One draftable lineage season: id, optional parent, methodology.pipeline."""
    lines = [
        f"id: {sid}",
        f'goal: "fixture {sid}"',
        "metric: m",
        "mode: fight",
        "methodology:",
        '  approach: "x"',
        "  evidence: []",
        "  primary_change:",
        "    type: add",
        "    node: execute",
        '    baseline: "b"',
        '    expected_band: "WIN if x"',
        '    rollback: "git revert"',
        f'    eval_window: "{sid}"',
        "  pipeline:",
        "    - phase: execute",
        "      primitive: execute",
        "      agents: writers",
        "      prompt: prompts/dev/dummy.md",
        "      writes: results.jsonl",
    ]
    if parent_id is not None:
        lines.insert(1, f"parent: {parent_id}")
    return "\n".join(lines) + "\n"


def _s130_campaign(tmp_path: Path, chain: list[tuple[str, str | None]]) -> Path:
    """A tmp campaign: seasons/<sid>.yaml over the .rumpun-state root; tmp only."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    for sid, parent_id in chain:
        (root / "seasons" / f"{sid}.yaml").write_text(
            _s130_season_text(sid, parent_id), encoding="utf-8"
        )
    return root


def _s130_plan(caplog: pytest.LogCaptureFixture, root: Path) -> str:
    """Plan the next season (s114) from s113; the draft must land; return the log."""
    with caplog.at_level(logging.DEBUG, logger="rumpun.evolve"):
        drafted = evolve.draft_next(root, root / "seasons" / "s113.yaml")
    assert drafted.is_file(), f"the plan never produced the draft: {drafted}"
    return caplog.text


def test_s130_pin1_exhausted_seal_round_trip(tmp_path: Path) -> None:
    """Seal EXHAUSTED with zero fronts; the reader reads the fields back whole."""
    root = tmp_path / "s130ledger"
    path = audit.seal_usefulness_assessment(
        root, "s130fx", "EXHAUSTED", [], satisfied=_S130_SATISFIED
    )
    body = "\n".join(path.read_text(encoding="utf-8").splitlines()[4:-1])
    assert body == (
        "verdict: EXHAUSTED\n"
        f"basis: {_S130_DEFAULT_BASIS}\n"
        "fronts:\n"
        "satisfied (recorded, not fronts):\n"
        "- exhaustion is the stopping criterion, answered honestly\n"
        "- the ledger stands as the campaign record"
    )
    data = audit.read_usefulness_assessment(path)
    expected = {
        "id": "usefulness-s130fx",
        "title": f"EXHAUSTED ({_S130_TITLE})",
        "verdict": "EXHAUSTED",
        "basis": _S130_DEFAULT_BASIS,
        "weight": "",
        "fronts": [],
        "satisfied": _S130_SATISFIED,
        "epics": [],
    }
    assert data == expected, f"the round-trip drifted: {data!r}"


def test_s130_pin2_exhausted_preflight() -> None:
    """usefulness_inputs passes the exhausted mapping to the seal unchanged."""
    verdict, fronts, satisfied, basis = audit.usefulness_inputs(
        {"verdict": "EXHAUSTED", "fronts": [], "satisfied": ["the ledger stands"]}
    )
    assert (verdict, fronts, satisfied, basis) == (
        "EXHAUSTED",
        [],
        ["the ledger stands"],
        None,
    )


def test_s130_pin3_exhausted_hint_stays_silent(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The EXHAUSTED newest seal is not due: the hint stays silent, the draft lands."""
    root = _s130_campaign(tmp_path, _S130_CHAIN)
    audit.seal_usefulness_assessment(root, "s113", "EXHAUSTED", [])
    text = _s130_plan(caplog, root)
    assert "assessment due" not in text, (
        f"the exhausted campaign was asked to continue: {text!r}"
    )


def test_s130_pin4_continue_drought_still_announces(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A verdict-bearing CONTINUE seal behind a full drought still announces."""
    root = _s130_campaign(tmp_path, _S130_CHAIN)
    audit.seal_usefulness_assessment(root, "s107", "CONTINUE", [_S130_FRONT])
    text = _s130_plan(caplog, root)
    assert "assessment due" in text, f"the hint went silent: {text!r}"
    assert "usefulness-s107" in text, f"the hint never named the seal: {text!r}"
