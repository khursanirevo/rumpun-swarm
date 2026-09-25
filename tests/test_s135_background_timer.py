"""s135 w1 pins - the stranded-wake gate: an armed timer cannot strand a lane unnoticed.

Spec source: the s135 w1 brief, issue #44 (the s85 incident): a writer
exited rc 0 with a background wake timer armed; the dependent verify
work behind the wake never ran, and nothing marked the exit. Ground
truth measured 2026-09-21: the exit read is engine._agent_snap; the
s112 incomplete key and the s124 reconciled key are the additive
precedents; the failed and crashed vocabulary stays unchanged.

The gate: once _agent_snap reads an rc-0 exit, it parses the lane's
agent.log stream-json; when the stream's LAST tool_use block arms a
background task (a tool_use whose input carries a truthy
run_in_background), the wake could never arrive in a session that
already ended, so the snap gains the additive key
stranded="background wake armed" -- the s112 incomplete precedent (an
additive key names the gap, the measured state and exit_code stay the
measured values). _write_results passes the key into the results row
(the s112 pass-through). Scope: the rc-0 "exited" state only; failed
and crashed writers keep the failure vocabulary; an arm followed by
more tool_use reads as a consumed wake, not a strand.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-21 on the pre-gate tree, pins 1 and 2 (KeyError
  on the stranded key); /tmp/s135-w1-pins-red.txt.
- GREEN captured 2026-09-21 post-gate; /tmp/s135-w1-pins-green.txt.
- Pins 3 and 4 are green on both sides by design: they pin the
  byte-identical clause and the gate's scope, so a later regression
  cannot mark a clean writer or excuse a failed one.

Bounds honored: tmp fixtures (writer dirs and stream-json logs
synthesized in tmp_path), no real timers, no claude spawns, nothing
copied from live .rumpun/runs state, offline, seconds-fast.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from rumpun import engine

S135W1_STALL_S = 900.0
S135W1_DEAD_PROC_START = 987654321  # no live pid's proc_start; the repo convention

# The stream-json shapes the gate reads: a foreground tool_use and the
# harness's background-arming shape (input.run_in_background truthy).
S135W1_FOREGROUND = {
    "type": "assistant",
    "message": {
        "content": [
            {"type": "tool_use", "id": "t1", "name": "Read",
             "input": {"file_path": "/tmp/x"}},
        ],
    },
}

S135W1_ARM = {
    "type": "assistant",
    "message": {
        "content": [
            {"type": "tool_use", "id": "t2", "name": "Bash",
             "input": {"command": "sleep 300", "run_in_background": True}},
        ],
    },
}


def _s135w1_stream_line(event: dict[str, Any]) -> str:
    return json.dumps(event) + "\n"


def _s135w1_meta(ws: Path) -> dict[str, Any]:
    """The engine's spawn-time workspace state.json shape, never-alive pid."""
    return {
        "name": ws.name,
        "route": "fixture",
        "cmd": "fixture-stranded-wake",
        "pid": 1,
        "proc_start": S135W1_DEAD_PROC_START,
        "started_at": time.time(),
    }


def _s135w1_write_ws(
    ws: Path, exit_code: str | None,
    log_events: list[dict[str, Any]] | None = None,
) -> Path:
    """Synthesize a dead writer workspace with a stream-json agent.log."""
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "state.json").write_text(
        json.dumps(_s135w1_meta(ws), indent=2) + "\n", encoding="utf-8"
    )
    if exit_code is not None:
        (ws / "exit").write_text(exit_code, encoding="utf-8")
    if log_events:
        (ws / "agent.log").write_text(
            "".join(_s135w1_stream_line(e) for e in log_events),
            encoding="utf-8",
        )
    return ws


def _s135w1_season(root: Path, sid: str) -> None:
    """The running season state the finalize path reads."""
    season = root / "runs" / sid / "_season"
    season.mkdir(parents=True, exist_ok=True)
    (season / "state.json").write_text(
        json.dumps(
            {
                "id": sid,
                "status": "running",
                "spawned": {
                    "w1": {"pid": 1, "proc_start": S135W1_DEAD_PROC_START},
                },
            }
        ),
        encoding="utf-8",
    )


# pin 1 - the gate at the snap layer: an rc-0 exit whose stream ends in
# a background-arming tool_use marks the unit STRANDED; the measured
# state and exit code are preserved.
def test_s135w1_exited_zero_with_armed_wake_tail_marks_stranded(
    tmp_path: Path,
) -> None:
    ws = _s135w1_write_ws(
        tmp_path / "w1", "0", [S135W1_FOREGROUND, S135W1_ARM]
    )
    snap = engine._agent_snap(ws, stall_s=S135W1_STALL_S)
    assert snap["state"] == "exited"
    assert snap["exit_code"] == 0
    assert snap["stranded"] == "background wake armed"


# pin 2 - the season record: the finalize writes the STRANDED mark into
# the agents entry and the results row; state, exit_code, seconds stay.
def test_s135w1_finalize_passes_stranded_into_state_and_row(
    tmp_path: Path,
) -> None:
    root = tmp_path
    sid = "s135f"
    _s135w1_write_ws(
        root / "runs" / sid / "w1", "0",
        [S135W1_FOREGROUND, S135W1_ARM],
    )
    _s135w1_season(root, sid)
    state = engine._finalize(root, sid, "completed", {})
    entry = state["agents"]["w1"]
    assert entry["state"] == "exited"
    assert entry["exit_code"] == 0
    assert entry["stranded"] == "background wake armed"
    row = json.loads(
        (root / "runs" / sid / "results.jsonl").read_text(encoding="utf-8")
    )
    assert row["unit"] == "w1"
    assert row["state"] == "exited"
    assert row["exit_code"] == 0
    assert row["stranded"] == "background wake armed"


# pin 3 - the byte-identical clause (green on both sides by design): an
# rc-0 exit with a clean foreground log gains nothing -- a malformed
# line and a system event change nothing, the last foreground tool_use
# is no arm; the snap carries only the baseline keys and the results row
# matches the pre-gate shape exactly.
def test_s135w1_rows_without_evidence_stay_byte_identical(
    tmp_path: Path,
) -> None:
    ws = _s135w1_write_ws(
        tmp_path / "w1", "0", [S135W1_FOREGROUND, S135W1_FOREGROUND]
    )
    log = ws / "agent.log"
    with log.open("a", encoding="utf-8") as fh:
        fh.write("{not json\n")  # malformed: skipped from classification
    # Notes present: the s112 gate stays quiet, so the baseline shape is
    # the pre-gate six keys -- the stranded clause is isolated here.
    (ws / "notes.md").write_text("lane notes\n", encoding="utf-8")
    ws2_events = [S135W1_FOREGROUND]
    ws2 = _s135w1_write_ws(
        tmp_path / "w2", "0", ws2_events
    )
    snap = engine._agent_snap(ws, stall_s=S135W1_STALL_S)
    assert snap["state"] == "exited"
    assert snap["exit_code"] == 0
    assert set(snap) == {
        "name", "route", "state", "exit_code", "started_at", "seconds",
    }
    root = tmp_path
    season = root / "runs" / "s135b"
    season.mkdir(parents=True)
    engine._write_results(root, "s135b", {"w1": snap})
    row = json.loads(
        (season / "results.jsonl").read_text(encoding="utf-8")
    )
    assert row == {
        "unit": "w1", "route": "fixture", "state": "exited",
        "exit_code": 0, "seconds": snap["seconds"],
    }
    snap2 = engine._agent_snap(ws2, stall_s=S135W1_STALL_S)
    assert "stranded" not in snap2


# pin 4 - the gate's scope (green on both sides by design): failed and
# crashed writers keep the failure vocabulary even with an armed-wake
# tail; an arm followed by more tool_use reads as a consumed wake, not a
# strand; a logless exited lane gains nothing.
def test_s135w1_failed_crashed_and_consumed_wake_stay_quiet(
    tmp_path: Path,
) -> None:
    for label, code in (("failed", "1"), ("crashed", "137")):
        ws = _s135w1_write_ws(tmp_path / label, code, [S135W1_ARM])
        snap = engine._agent_snap(ws, stall_s=S135W1_STALL_S)
        assert snap["state"] == label
        assert "stranded" not in snap, label
    consumed = _s135w1_write_ws(
        tmp_path / "consumed", "0", [S135W1_ARM, S135W1_FOREGROUND]
    )
    snap = engine._agent_snap(consumed, stall_s=S135W1_STALL_S)
    assert snap["state"] == "exited"
    assert "stranded" not in snap
    logless = _s135w1_write_ws(tmp_path / "nolog", "0", [])
    snap = engine._agent_snap(logless, stall_s=S135W1_STALL_S)
    assert snap["state"] == "exited"
    assert "stranded" not in snap
