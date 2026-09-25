"""s112 w1 pins - the notes gate: a notes-less writer exit marks INCOMPLETE.

Spec source: the s112 w1 brief. Twice (s108 w1, s111 w1) a writer exited 0
without notes.md and only the brief's REQUIRED clause stood guard; the
clause failed twice. Ground truth measured 2026-09-20: the s111 season
state agents entry and the results row read state "exited" / exit_code 0
with no notes.md at .rumpun/runs/s111/w1/notes.md.

The gate: once _agent_snap reads a writer's rc-0 exit, it checks
ws/notes.md; absent, the snap gains the additive key
incomplete="notes.md missing" -- the terminated_budget precedent (an
additive key names the gap, the measured state and exit_code stay
untouched). _write_results passes the key into the results row, so the
season record names the gap on both surfaces. Notes present -> the snap
gains nothing. Scope: the rc-0 "exited" state only ("instead of a bare
exit 0"); failed and crashed writers keep the failure vocabulary, no
notes-gap marker dresses a real error exit.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 on the pre-gate tree, pins 1 and 4
  (KeyError on the marker); /tmp/s112-w1-pins-red.txt.
- GREEN captured 2026-09-20 post-gate; /tmp/s112-w1-pins-green.txt.
- Pins 2 and 3 are green on both sides by design: they pin the
  untouched-entry clause and the gate's scope, so a later regression
  cannot mark a healthy writer or excuse a failed one.

Bounds honored: fixtures only (writer dirs synthesized in tmp_path, no
claude spawns, nothing copied from live .rumpun/runs state), offline,
seconds-fast.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from rumpun import engine

S112W1_STALL_S = 900.0
S112W1_DEAD_PROC_START = 987654321  # no live pid's proc_start; the repo convention


def _s112w1_meta(ws: Path) -> dict[str, Any]:
    """The engine's spawn-time workspace state.json shape, never-alive pid."""
    return {
        "name": ws.name,
        "route": "fixture",
        "cmd": "fixture-notes-gate",
        "pid": 1,
        "proc_start": S112W1_DEAD_PROC_START,
        "started_at": time.time(),
    }


def _s112w1_write_ws(ws: Path, exit_code: str | None) -> Path:
    """Synthesize a dead writer workspace; exit_code None -> no exit file."""
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "state.json").write_text(
        json.dumps(_s112w1_meta(ws), indent=2) + "\n", encoding="utf-8"
    )
    if exit_code is not None:
        (ws / "exit").write_text(exit_code, encoding="utf-8")
    return ws


def _s112w1_season(root: Path, sid: str) -> None:
    """The running season state the finalize path reads."""
    season = root / "runs" / sid / "_season"
    season.mkdir(parents=True, exist_ok=True)
    (season / "state.json").write_text(
        json.dumps(
            {
                "id": sid,
                "status": "running",
                "spawned": {
                    "w1": {"pid": 1, "proc_start": S112W1_DEAD_PROC_START},
                },
            }
        ),
        encoding="utf-8",
    )


# pin 1 - the gate at the snap layer: a writer that exits 0 without
# notes.md marks the unit INCOMPLETE (the additive key names the gap);
# the measured state and exit code are preserved.
def test_s112w1_exited_zero_without_notes_marks_incomplete(
    tmp_path: Path,
) -> None:
    ws = _s112w1_write_ws(tmp_path / "w1", "0")
    snap = engine._agent_snap(ws, stall_s=S112W1_STALL_S)
    assert snap["state"] == "exited"
    assert snap["exit_code"] == 0
    assert snap["incomplete"] == "notes.md missing"


# pin 2 - the untouched-entry clause (green on both sides by design):
# notes.md present, the snap gains nothing; the record is the pre-gate
# shape.
def test_s112w1_notes_present_snap_untouched(tmp_path: Path) -> None:
    ws = _s112w1_write_ws(tmp_path / "w1", "0")
    (ws / "notes.md").write_text("lane notes\n", encoding="utf-8")
    snap = engine._agent_snap(ws, stall_s=S112W1_STALL_S)
    assert snap["state"] == "exited"
    assert snap["exit_code"] == 0
    assert "incomplete" not in snap


# pin 3 - the gate's scope (green on both sides by design): failed and
# crashed writers keep the honest failure vocabulary; the notes gate must
# not dress a real error exit as the notes gap.
def test_s112w1_failed_and_crashed_keep_failure_vocabulary(
    tmp_path: Path,
) -> None:
    cases = (("failed", "1", "failed"), ("crashed", "137", "crashed"))
    for label, code, want_state in cases:
        ws = _s112w1_write_ws(tmp_path / label, code)
        snap = engine._agent_snap(ws, stall_s=S112W1_STALL_S)
        assert snap["state"] == want_state, label
        assert snap["exit_code"] == int(code), label
        assert "incomplete" not in snap, label


# pin 4 - the season record: the finalize writes the INCOMPLETE mark into
# the agents entry and the results row; the entry keeps state, exit_code,
# seconds.
def test_s112w1_finalize_marks_incomplete_in_state_and_row(
    tmp_path: Path,
) -> None:
    root = tmp_path
    sid = "s112f"
    ws = _s112w1_write_ws(root / "runs" / sid / "w1", "0")
    assert not (ws / "notes.md").exists()
    _s112w1_season(root, sid)
    state = engine._finalize(root, sid, "completed", {})
    entry = state["agents"]["w1"]
    assert entry["state"] == "exited"
    assert entry["exit_code"] == 0
    assert entry["incomplete"] == "notes.md missing"
    row = json.loads(
        (root / "runs" / sid / "results.jsonl").read_text(encoding="utf-8")
    )
    assert row["unit"] == "w1"
    assert row["state"] == "exited"
    assert row["exit_code"] == 0
    assert row["incomplete"] == "notes.md missing"
