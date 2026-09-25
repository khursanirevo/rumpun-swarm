"""s92 w1 pins - the s91 kill-detection gap: signal deaths record crashed.

Spec sources: the s92 w1 brief (kill-detection gap), the s91 disclosure
(DESIGN.md s91 row: "the engine recorded exit 0 - a kill-detection gap
disclosed"; the s91 w2 notes: w1's background suite task shows status
"killed" in the log tail), and the s91 w1 artifacts measured 2026-09-17
(.rumpun/runs/s91/w1: the exit file 1 byte "0", agent.log tail = result
event + task_updated status "killed" + task_notification status
"stopped", no notes.md).

Measured mechanism (repro_kill.py + repro_kill.out, 2026-09-17):
- the spawn wrapper (engine._wrap_spawn_cmd, factored verbatim from the
  spawn loop) already records a payload signal death faithfully: the
  exit file carries 128+N (dash propagates it through the pipeline);
- the pre-fix reading side was the lie: engine._agent_snap mapped
  rc 137 to "failed" (a real-error vocabulary) instead of "crashed";
- the s91 exit-0 shape is rc-blind: a claude that kills its own
  background task and exits 0 records "0" honestly at the rc layer; the
  honest kill record lives in the stream (task_updated status "killed").
- the stall clock never applies to terminal agents (the exit-file branch
  short-circuits), so the s60/s24 clocks were correct to stay silent for
  w1; they fire only on live writers whose every progress source went
  quiet past stall_s.

Color history (the s91 w2 evidence-trail convention):
- RED captured 2026-09-17 23:30 on the pre-mapping tree (wrapper helper
  already extracted, behavior-neutral): repro_kill.out measured
  payload-sigkill -> snap state=failed exit_code=137, and the
  s91-bg-kill shape -> exited 0.
- GREEN captured 2026-09-17 against the fixed tree (this file, first
  run post-mapping; see the run log in the w1 workspace notes.md).
- The bg-kill witness pin (test_s92w1_bg_task_kill_exits_zero) is green
  on both sides by design: it pins the rc blind spot as the measured
  mechanism, so the record names what rc-level detection cannot see.

Bounds honored: fixtures only (real /bin/sh payloads, no claude, no live
season spawns), offline, seconds-fast.
"""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from rumpun import engine

S92W1_KILL_RC = 137  # 128 + SIGKILL(9); dash propagates it through the pipeline
S92W1_STALL_S = 900.0
S92W1_DEAD_PROC_START = 987654321  # no live pid's proc_start; the repo convention


def _s92w1_meta(ws: Path, cmd: str, pid: int, proc_start: int | None) -> dict[str, Any]:
    """The engine's spawn-time workspace state.json shape."""
    return {
        "name": ws.name,
        "route": "fixture",
        "cmd": cmd,
        "pid": pid,
        "proc_start": proc_start,
        "started_at": time.time(),
    }


def _s92w1_dead_meta(ws: Path, cmd: str) -> dict[str, Any]:
    """Meta whose pid can never read alive (the test_rumpun convention)."""
    return _s92w1_meta(ws, cmd, 1, S92W1_DEAD_PROC_START)


def _s92w1_write_ws(ws: Path, meta: dict[str, Any]) -> None:
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "state.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )


def _s92w1_spawn_payload(ws: Path, cmd: str) -> subprocess.Popen:
    """Spawn the engine's own wrapper over cmd, engine shape (log, cwd, meta)."""
    exit_file = ws / "exit"
    wrapped = engine._wrap_spawn_cmd(cmd, exit_file)
    with (ws / "agent.log").open("wb") as log_f:
        proc = subprocess.Popen(
            ["/bin/sh", "-c", wrapped], stdout=log_f, stderr=log_f,
            cwd=ws, start_new_session=True,
        )
    meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    meta["pid"] = proc.pid
    meta["proc_start"] = engine._proc_start_ticks(proc.pid)
    (ws / "state.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    return proc


def _s92w1_reap(proc: subprocess.Popen) -> None:
    proc.wait(timeout=30)


def _s92w1_alive_sleeper() -> tuple[subprocess.Popen, int | None]:
    proc = subprocess.Popen(["sleep", "30"], start_new_session=True)
    return proc, engine._proc_start_ticks(proc.pid)


def _s92w1_kill_sleeper(proc: subprocess.Popen) -> None:
    with contextlib.suppress(ProcessLookupError):
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait(timeout=30)


# pin 1 - the wrapper records real exits and signal deaths distinctly, and
# the reading side maps them honestly (0 -> exited, 1 -> failed, 137 -> crashed).
def test_s92w1_exit_file_distinguishes_real_exit_from_signal_death(
    tmp_path: Path,
) -> None:
    cases = (
        ("exit-0", "true", b"0", "exited"),
        ("exit-1", "sh -c 'exit 1'", b"1", "failed"),
        ("sigkill", "sh -c 'kill -9 $$'", b"137", "crashed"),
    )
    for label, cmd, want_bytes, want_state in cases:
        ws = tmp_path / label
        _s92w1_write_ws(ws, _s92w1_dead_meta(ws, cmd))
        proc = _s92w1_spawn_payload(ws, cmd)
        _s92w1_reap(proc)
        assert (ws / "exit").read_bytes() == want_bytes, label
        snap = engine._agent_snap(ws, stall_s=S92W1_STALL_S)
        assert snap["state"] == want_state, label
        assert snap["exit_code"] == int(want_bytes.decode()), label
        assert snap["state"] in engine.TERMINAL, label


# pin 2 - the killed-writer fixture: a payload killed by SIGKILL mid-run
# records the killed state (crashed), never exited, never stalled.
def test_s92w1_killed_writer_fixture_records_crashed(tmp_path: Path) -> None:
    ws = tmp_path / "w1"
    _s92w1_write_ws(ws, _s92w1_dead_meta(ws, "sh -c 'kill -9 $$'"))
    proc = _s92w1_spawn_payload(ws, "sh -c 'kill -9 $$'")
    _s92w1_reap(proc)
    snap = engine._agent_snap(ws, stall_s=S92W1_STALL_S)
    assert snap["state"] == "crashed"
    assert snap["exit_code"] == S92W1_KILL_RC
    assert snap["state"] in engine.TERMINAL
    # the stall clock cannot misfire on a terminal agent at any threshold
    snap_now = engine._agent_snap(ws, stall_s=0.001)
    assert snap_now["state"] == "crashed"


# pin 3 - the season record is honest about a crashed writer: a completed
# finalize downgrades to failed, the agent snap and results row carry
# crashed / 137.
def test_s92w1_crashed_writer_downgrades_season_to_failed(tmp_path: Path) -> None:
    root = tmp_path
    sid = "s92f"
    ws = root / "runs" / sid / "w1"
    _s92w1_write_ws(ws, _s92w1_dead_meta(ws, "sh -c 'kill -9 $$'"))
    (ws / "exit").write_text("137", encoding="utf-8")
    (ws / "agent.log").write_bytes(b"")
    (root / "runs" / sid / "_season").mkdir(parents=True, exist_ok=True)
    (root / "runs" / sid / "_season" / "state.json").write_text(
        json.dumps(
            {
                "id": sid,
                "status": "running",
                "spawned": {"w1": {"pid": 1, "proc_start": S92W1_DEAD_PROC_START}},
            }
        ),
        encoding="utf-8",
    )
    state = engine._finalize(root, sid, "completed", {})
    assert state["status"] == "failed"
    assert state["agents"]["w1"]["state"] == "crashed"
    assert state["agents"]["w1"]["exit_code"] == S92W1_KILL_RC
    row = json.loads(
        (root / "runs" / sid / "results.jsonl").read_text(encoding="utf-8")
    )
    assert row["unit"] == "w1"
    assert row["state"] == "crashed"
    assert row["exit_code"] == S92W1_KILL_RC


# pin 4 - the s91 mechanism witness (green on both sides by design): a
# payload that kills its own background child and exits 0 records "0" --
# the rc layer cannot see the kill; the stream carries the honest record.
def test_s92w1_bg_task_kill_exits_zero(tmp_path: Path) -> None:
    ws = tmp_path / "w1"
    cmd = "sh -c 'sleep 30 & p=$!; sleep 0.3; kill -9 $p; exit 0'"
    _s92w1_write_ws(ws, _s92w1_dead_meta(ws, cmd))
    proc = _s92w1_spawn_payload(ws, cmd)
    _s92w1_reap(proc)
    assert (ws / "exit").read_bytes() == b"0"
    snap = engine._agent_snap(ws, stall_s=S92W1_STALL_S)
    assert snap["state"] == "exited"
    assert snap["exit_code"] == 0


# pin 5 - the stall clock fires on a live writer whose every progress
# source (scanner-stamped log growth; no tool use, no workspace writes)
# went quiet past stall_s.
def test_s92w1_stall_clock_fires_on_silent_writer(tmp_path: Path) -> None:
    ws = tmp_path / "w1"
    proc, proc_start = _s92w1_alive_sleeper()
    try:
        meta = _s92w1_meta(ws, "fixture-sleeper", proc.pid, proc_start)
        meta["started_at"] = time.time() - 3600.0  # silent since spawn
        meta["log_size"] = 10
        meta["stream_offset"] = 10
        meta["last_progress"] = time.time() - 3600.0
        _s92w1_write_ws(ws, meta)
        (ws / "agent.log").write_bytes(b"init line\n")
        snap = engine._agent_snap(ws, stall_s=S92W1_STALL_S)
        assert snap["state"] == "stalled"
    finally:
        _s92w1_kill_sleeper(proc)


# pin 6 - the log-growth clock holds on growth (two layers, the runtime
# chain): the scanner stamps last_progress on appended bytes, and the snap
# holds the clock open on the fresh stamp -- a silent writer with a growing
# log is not idle.
def test_s92w1_growing_log_is_not_idle(tmp_path: Path) -> None:
    ws = tmp_path / "runs" / "s92scan" / "w1"
    proc, proc_start = _s92w1_alive_sleeper()
    try:
        meta = _s92w1_meta(ws, "fixture-sleeper", proc.pid, proc_start)
        meta["started_at"] = time.time() - 3600.0  # clock held by the stamp, not spawn
        meta["log_size"] = 10
        meta["stream_offset"] = 10
        meta["last_progress"] = time.time() - 3600.0
        ws.mkdir(parents=True)
        (ws / "agent.log").write_bytes(b"init line\n")
        (ws / "state.json").write_text(
            json.dumps(meta, indent=2) + "\n", encoding="utf-8"
        )
        with (ws / "agent.log").open("ab") as fh:
            fh.write(b"x" * 30 + b"\n")  # appended bytes, no tool events
        engine._scan_agent_stream(ws, meta)
        assert meta["last_progress"] > time.time() - 60.0
        assert meta["log_size"] == 41
        assert meta["stream_offset"] == 41
        snap = engine._agent_snap(ws, stall_s=S92W1_STALL_S)
        assert snap["state"] == "running"
    finally:
        _s92w1_kill_sleeper(proc)
