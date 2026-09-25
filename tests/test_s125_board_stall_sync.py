"""s125 w1 pins — the board sync carries the stall.

Spec source: the s125 w1 brief. The heartbeat publishes the stall
events and the report renders them; the board is where the operator
reads, so the s119 mirror sync carries the stall onto the season's
card: the stall line names the lane and the last-progress stamp.

Offline: the pins run the pure mirror logic over fixture events in tmp
(the heartbeat's own file shape, hand-written) -- stall_marks,
mirror_card_body, mirror_plan, mirror_sync with injected seams
(trail_fn, run). No gh call anywhere in this file.

Contract these pins hold -- src/rumpun/board.py:

1. stall_marks(root): {sid: {lane: iso}} over the events bus -- the
   report's _stall_marks read (s124 w1), imported not re-derived.
   A missing events dir is the quiet bus ({}); foreign or unparseable
   bytes skip; one lane per file; a missing last-progress renders the
   report's absence mark.
2. mirror_card_body: the s119 three-line body, plus a fourth line
   "stalled: <lane> since <iso>, ..." (lanes sorted) exactly when the
   season's stall map is nonempty. No stall, no mark: the bytes match
   the s119 body exactly.
3. mirror_plan: only seasons in the truth plan (nothing invented); a
   stall naming a season with no verdict row plans nothing; the stall
   rides create and update bodies alike.
4. Idempotence (pure): apply the stalled plan to fixture cards,
   re-plan -> empty.
5. A swept event is honest drift: the next plan updates the card back
   to the plain body (the mark drops when the event drops).
6. mirror_sync end to end offline: the first sync edits the card to
   the stalled bytes; the second sync runs zero gh calls; a campaign
   with no events keeps the s119 bytes (guard: green on both sides by
   design).

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 pre-implementation; /tmp/s125-w1-pins-red.txt.
- GREEN captured 2026-09-20 post-implementation;
  /tmp/s125-w1-pins-green.txt.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

logger = logging.getLogger(__name__)

A1 = 1780000000.0
A2 = 1780000123.0


def _board_module():
    """Import rumpun.board; fail naming the spec reason when unlanded."""
    try:
        from rumpun import board as board_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/board.py missing/unimportable: {exc}")
    return board_module


def _root(tmp_path: Path) -> Path:
    """A fresh .rumpun root: rumpun.yaml, empty ledger, runs, seasons."""
    campaign = tmp_path / "s125proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        "autonomy:\n  stage: manual\n", encoding="utf-8"
    )
    return root


def _sealed_harvest(root: Path, sid: str) -> Path:
    """Append the <sid>-harvest record through akar itself; the seal is real."""
    from rumpun import akar

    return akar.append_record(
        root,
        f"{sid}-harvest",
        f"season {sid} harvest",
        f"season {sid}: completed\nverdict: WIN\n",
    )


def _verdicts(root: Path, sid: str, *rows: str) -> Path:
    """Write runs/<sid>/verdicts.jsonl with the fixture rows verbatim."""
    path = root / "runs" / sid / "verdicts.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(row + "\n" for row in rows), encoding="utf-8")
    return path


def _card(number: int, body: str) -> dict[str, Any]:
    """One issue_trail row: number, state, body (the s76 parser shape)."""
    return {"number": number, "state": "OPEN", "body": body}


def _event(root: Path, sid: str, lane: str, anchor: float) -> Path:
    """Hand-write one lane-stalled event (loop.emit_lane_stalled's shape)."""
    bus = root / "events"
    bus.mkdir(parents=True, exist_ok=True)
    path = bus / f"lane-stalled-{sid}-{lane}.json"
    path.write_text(
        json.dumps(
            {
                "kind": "lane-stalled",
                "season": sid,
                "lane": lane,
                "last_progress": anchor,
                "at": anchor + 7.0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _iso(anchor: float) -> str:
    """The report's ISO render of a last-progress anchor (UTC, seconds)."""
    return datetime.fromtimestamp(anchor, tz=timezone.utc).isoformat(
        timespec="seconds"
    )


def test_s125bs_stall_marks_read_the_bus(tmp_path: Path) -> None:
    """The mark's source on the board side: one lane per event file,
    seasons grouped, the ISO render of the last-progress anchor."""
    board = _board_module()
    root = _root(tmp_path)
    _event(root, "s1", "w2", A2)
    _event(root, "s1", "w1", A1)
    _event(root, "s2", "w1", A1)
    assert board.stall_marks(root) == {
        "s1": {"w1": _iso(A1), "w2": _iso(A2)},
        "s2": {"w1": _iso(A1)},
    }, f"marks: {board.stall_marks(root)!r}"
    assert board.stall_marks(tmp_path / "quiet-root") == {}, (
        "a missing events dir is the quiet bus"
    )


def test_s125bs_stall_marks_skip_foreign_bytes(tmp_path: Path) -> None:
    """Foreign and broken bus bytes never become marks: unparseable JSON,
    a foreign file name, a wrong kind under a stall name, an event with
    no lane. An event with no last-progress renders the report's
    absence mark."""
    board = _board_module()
    root = _root(tmp_path)
    bus = root / "events"
    bus.mkdir(parents=True)
    (bus / "lane-stalled-s9-w0.json").write_text("{not json", encoding="utf-8")
    (bus / "season-completed-s9.json").write_text(
        json.dumps({"kind": "season-completed", "season": "s9"}) + "\n",
        encoding="utf-8",
    )
    (bus / "lane-stalled-s9-fake.json").write_text(
        json.dumps(
            {"kind": "season-completed", "season": "s9", "lane": "w3"}
        )
        + "\n",
        encoding="utf-8",
    )
    (bus / "lane-stalled-s9-w2.json").write_text(
        json.dumps({"kind": "lane-stalled", "season": "s9", "lane": ""}) + "\n",
        encoding="utf-8",
    )
    (bus / "lane-stalled-s9-w9.json").write_text(
        json.dumps({"kind": "lane-stalled", "season": "s9", "lane": "w9"}) + "\n",
        encoding="utf-8",
    )
    assert board.stall_marks(root) == {"s9": {"w9": "-"}}, (
        f"marks: {board.stall_marks(root)!r}"
    )


def test_s125bs_card_body_carries_the_stall() -> None:
    """The card bytes: the s119 three lines, plus the stall line naming
    the lane and the last-progress stamp, lanes sorted, only when the
    season's stall map is nonempty. No stall, no mark."""
    board = _board_module()
    plain = "season: s125f\nverdict: WIN\nbasis: b"
    assert board.mirror_card_body("s125f", "WIN", "b") == plain
    assert board.mirror_card_body("s125f", "WIN", "b", {}) == plain, (
        "an empty stall map marks nothing"
    )
    stalled = board.mirror_card_body(
        "s125f", "WIN", "b", {"w2": _iso(A2), "w1": _iso(A1)}
    )
    assert stalled == (
        plain + f"\nstalled: w1 since {_iso(A1)}, w2 since {_iso(A2)}"
    ), f"body: {stalled!r}"


def test_s125bs_plan_marks_only_truth_seasons(tmp_path: Path) -> None:
    """The stall rides the plan of the season it marks: create bodies
    carry the stall line; a season with no stall keeps the plain body;
    a stall naming a season with no verdict row plans nothing (nothing
    invented)."""
    board = _board_module()
    root = _root(tmp_path)
    _event(root, "s125f", "w1", A1)
    _event(root, "s120", "w2", A2)
    stalls = board.stall_marks(root)
    truth = {
        "s125f": ("WIN", "s125f-harvest@ab12cd34"),
        "s98": ("LOSS", "no sealed s98-harvest record"),
    }
    plan = board.mirror_plan(truth, [], stalls)
    assert [(row["action"], row["sid"]) for row in plan] == [
        ("create", "s125f"),
        ("create", "s98"),
    ], f"plan: {[(r['action'], r['sid']) for r in plan]!r}"
    assert plan[0]["body"] == (
        "season: s125f\nverdict: WIN\nbasis: s125f-harvest@ab12cd34"
        f"\nstalled: w1 since {_iso(A1)}"
    ), f"body: {plan[0]['body']!r}"
    assert plan[1]["body"] == (
        "season: s98\nverdict: LOSS\nbasis: no sealed s98-harvest record"
    ), "no stall, no mark"


def test_s125bs_second_sync_changes_nothing(tmp_path: Path) -> None:
    """Idempotence (pure): apply the stalled plan to the fixture cards,
    re-plan -> empty -- the stalled bytes match the stalled truth."""
    board = _board_module()
    root = _root(tmp_path)
    _event(root, "s125f", "w1", A1)
    truth = {"s125f": ("WIN", "s125f-harvest@ab12cd34")}
    stalls = board.stall_marks(root)
    cards: list[dict[str, Any]] = []
    plan1 = board.mirror_plan(truth, cards, stalls)
    assert [row["action"] for row in plan1] == ["create"], f"plan1: {plan1!r}"
    cards.append(_card(950, plan1[0]["body"]))
    assert board.mirror_plan(truth, cards, stalls) == [], (
        "the second run must plan nothing"
    )


def test_s125bs_swept_event_drops_the_mark(tmp_path: Path) -> None:
    """The mark is the event's shadow: while the event stands the stalled
    card matches (no plan); once the heartbeat sweeps it, the same card
    drifts and the plan updates it back to the plain body."""
    board = _board_module()
    root = _root(tmp_path)
    _event(root, "s125f", "w1", A1)
    truth = {"s125f": ("WIN", "s125f-harvest@ab12cd34")}
    plain = "season: s125f\nverdict: WIN\nbasis: s125f-harvest@ab12cd34"
    stalled = board.mirror_card_body(
        "s125f", "WIN", truth["s125f"][1], board.stall_marks(root)["s125f"]
    )
    cards = [_card(951, stalled)]
    assert board.mirror_plan(truth, cards, board.stall_marks(root)) == []
    (root / "events" / "lane-stalled-s125f-w1.json").unlink()
    plan = board.mirror_plan(truth, cards, board.stall_marks(root))
    assert [(r["action"], r["sid"], r["number"]) for r in plan] == [
        ("update", "s125f", 951)
    ], f"plan: {plan!r}"
    assert plan[0]["body"] == plain, "the mark drops with the event"


def test_s125bs_sync_carries_the_stall_end_to_end(tmp_path: Path) -> None:
    """End to end offline: a stalled season's drifted card edits to the
    stalled bytes through the one run seam; the second sync runs zero
    gh calls and renders the honest nothing."""
    board = _board_module()
    root = _root(tmp_path)
    _sealed_harvest(root, "s125f")
    _verdicts(root, "s125f", '{"season": "s125f", "verdict": "WIN"}')
    _event(root, "s125f", "w1", A1)
    basis = board.ledger_truth(root)["s125f"][1]
    plain = f"season: s125f\nverdict: WIN\nbasis: {basis}"
    stalled = plain + f"\nstalled: w1 since {_iso(A1)}"
    cards = [_card(960, "season: s125f\nverdict: WIN\nbasis: drifted")]
    seen: list[list[str]] = []

    def run(argv: list[str]) -> str:
        seen.append(list(argv))
        return ""

    board.mirror_sync(root, dry_run=False, trail_fn=lambda: cards, run=run)
    assert len(seen) == 1, f"seam: {seen!r}"
    assert seen[0][:3] == ["gh", "issue", "edit"], f"seam: {seen[0]!r}"
    assert seen[0][-1] == stalled, f"the card body: {seen[0][-1]!r}"

    cards[:] = [_card(960, seen[0][-1])]
    seen.clear()
    receipt = board.mirror_sync(
        root, dry_run=False, trail_fn=lambda: cards, run=run
    )
    assert seen == [], f"the second sync runs nothing: {seen!r}"
    assert "no drift: the board matches the ledger" in receipt, f"{receipt!r}"


def test_s125bs_sync_without_events_keeps_the_s119_bytes(
    tmp_path: Path,
) -> None:
    """Guard (green on both sides by design): a quiet bus never marks --
    the sync body stays the s119 three-line body exactly."""
    board = _board_module()
    root = _root(tmp_path)
    _sealed_harvest(root, "s125f")
    _verdicts(root, "s125f", '{"season": "s125f", "verdict": "WIN"}')
    basis = board.ledger_truth(root)["s125f"][1]
    plain = f"season: s125f\nverdict: WIN\nbasis: {basis}"
    cards = [_card(961, "season: s125f\nverdict: WIN\nbasis: drifted")]
    seen: list[list[str]] = []

    def run(argv: list[str]) -> str:
        seen.append(list(argv))
        return ""

    board.mirror_sync(root, dry_run=False, trail_fn=lambda: cards, run=run)
    assert len(seen) == 1, f"seam: {seen!r}"
    assert seen[0][-1] == plain, "no stall, no mark: the s119 bytes exactly"
