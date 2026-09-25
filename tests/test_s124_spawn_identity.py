"""s124 w2 pins -- the running state reconciles against live processes.

Spec source: the s124 w2 brief. The scar: the s109 restart left a dead
runner reading "running" in the durable season state until a human
looked. The reaper (issue #33, the sibling's PR) handles boot; the read
surface is this pin's subject. Ground truth measured 2026-09-20: the
_agent_snap elif chain (exit file, terminated marker, _alive, else)
reads a snap whose pid or proc_start no longer matches /proc as
crashed, and read_status recomputes agent snaps from /proc for running
seasons -- the M1/P36 split (read_persisted_status never reads /proc;
read_status does, for running seasons).

The s124 w2 rule: the mismatch -> crashed mapping holds, never running,
and the status output names the reconciliation. The additive key
reconciled=... names the /proc mismatch on the crashed snap (the
terminated_budget and incomplete precedent: an additive key names the
gap, the measured state stays untouched).

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 on the pre-key tree: pins 4 and 5 (the
  missing reconciled key); /tmp/s124-w2-pins-red.txt.
- GREEN captured 2026-09-20 post-key; /tmp/s124-w2-pins-green.txt.
- Pins 1-3 and 6-8 are green on both sides by design: they pin the
  elif chain's existing mapping (gone, recycled, no-pid -> crashed)
  and the scope guards (a live agent takes no note; an exit-code crash
  carries durable proof and takes no note; the terminated marker reads
  terminated; the persisted record stays running under the M1 split).

Bounds honored: the /proc reader is monkeypatched to a fake stat tree
in tmp_path (same stat format); the real process table is never
touched. Offline, seconds-fast, fixtures only.
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

import pytest

from rumpun import engine

S124W2_STALL_S = 2700.0
S124W2_PID = 4242
S124W2_START = 100
S124W2_LIVE_START = 999


class _FakeProc:
    """A /proc stand-in rooted in tmp, same stat format.

    The engine's reader (engine._proc_start_ticks) is monkeypatched to
    parse this tree, so no pin reads the real process table (the s124
    w2 fixture discipline).
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    def spawn(self, pid: int, start: int) -> None:
        d = self.root / str(pid)
        d.mkdir(parents=True, exist_ok=True)
        # pid (comm) state ... starttime: starttime is field 22, tail
        # index 19 after the ')' (state is tail[0]); 18 filler fields
        # sit between state and starttime.
        (d / "stat").write_text(
            f"{pid} (fixture) S " + "0 " * 18 + str(start),
            encoding="utf-8",
        )

    def kill(self, pid: int) -> None:
        shutil.rmtree(self.root / str(pid), ignore_errors=True)

    def stat(self, pid: int) -> int | None:
        try:
            text = (self.root / str(pid) / "stat").read_text(encoding="utf-8")
        except OSError:
            return None
        tail = text[text.rfind(")") + 1:].split()
        if tail and tail[0] == "Z":
            return None  # zombie: dead until reaped, never alive
        return int(tail[19]) if len(tail) > 19 else None


@pytest.fixture
def fake_proc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _FakeProc:
    proc = _FakeProc(tmp_path / "proc")
    monkeypatch.setattr(engine, "_proc_start_ticks", proc.stat)
    return proc


def _meta(name: str, pid: int | None, start: int | None) -> dict[str, Any]:
    """The engine's spawn-time workspace state.json shape (subset)."""
    return {
        "name": name,
        "route": "fixture",
        "pid": pid,
        "proc_start": start,
        "started_at": time.time(),
    }


def _season(root: Path, sid: str, agents: dict[str, dict[str, Any]]) -> Path:
    """A running season with per-agent workspaces (engine shapes)."""
    sdir = root / "runs" / sid
    (sdir / "_season").mkdir(parents=True)
    (sdir / "_season" / "state.json").write_text(
        json.dumps(
            {
                "id": sid,
                "status": "running",
                "started_at": 1.0,
                "stall_s": S124W2_STALL_S,
                "spawned": {
                    name: {"pid": m["pid"], "proc_start": m["proc_start"]}
                    for name, m in agents.items()
                },
            }
        ),
        encoding="utf-8",
    )
    for name, m in agents.items():
        ws = sdir / name
        ws.mkdir()
        (ws / "state.json").write_text(json.dumps(m), encoding="utf-8")
    return sdir


def test_pin1_pid_gone_reads_crashed_never_running(fake_proc, tmp_path):
    """Dead pid -> crashed on the live read; the durable record stays
    running (the M1/P36 split) and the read never mutates it."""
    root = tmp_path
    _season(root, "s1", {"a1": _meta("a1", S124W2_PID, S124W2_START)})
    fake_proc.spawn(S124W2_PID, S124W2_START)
    fake_proc.kill(S124W2_PID)  # the process exited between writes
    persisted = engine.read_persisted_status(root, "s1")
    assert persisted["status"] == "running"  # M1: no /proc, no mutation
    snap = engine.read_status(root, "s1")["agents"]["a1"]
    assert snap["state"] == "crashed"  # never running
    assert snap["exit_code"] is None
    assert engine.read_persisted_status(root, "s1")["status"] == "running"


def test_pin2_pid_recycled_reads_crashed(fake_proc, tmp_path):
    """PID-reuse guard: the pid lives again with a different start."""
    root = tmp_path
    _season(root, "s1", {"a1": _meta("a1", S124W2_PID, S124W2_START)})
    fake_proc.spawn(S124W2_PID, S124W2_LIVE_START)
    snap = engine.read_status(root, "s1")["agents"]["a1"]
    assert snap["state"] == "crashed"


def test_pin3_no_pid_intent_reads_crashed(fake_proc, tmp_path):
    """The pid-None spawn intent (crash between Popen and the pid save)."""
    root = tmp_path
    _season(root, "s1", {"a1": _meta("a1", None, None)})
    snap = engine.read_status(root, "s1")["agents"]["a1"]
    assert snap["state"] == "crashed"
    assert snap["exit_code"] is None


def test_pin4_status_names_gone_pid(fake_proc, tmp_path):
    """The status output names the reconciliation: pid gone."""
    root = tmp_path
    _season(root, "s1", {"a1": _meta("a1", S124W2_PID, S124W2_START)})
    fake_proc.spawn(S124W2_PID, S124W2_START)
    fake_proc.kill(S124W2_PID)
    snap = engine.read_status(root, "s1")["agents"]["a1"]
    assert snap["state"] == "crashed"
    assert snap["reconciled"] == f"pid {S124W2_PID} gone"


def test_pin5_status_names_recycled_pid(fake_proc, tmp_path):
    """The status output names the reconciliation: pid recycled."""
    root = tmp_path
    _season(root, "s1", {"a1": _meta("a1", S124W2_PID, S124W2_START)})
    fake_proc.spawn(S124W2_PID, S124W2_LIVE_START)
    snap = engine.read_status(root, "s1")["agents"]["a1"]
    assert snap["state"] == "crashed"
    assert snap["reconciled"] == (
        f"pid {S124W2_PID} start {S124W2_START} != live {S124W2_LIVE_START}"
    )


def test_pin6_live_agent_takes_no_note(fake_proc, tmp_path):
    """A matching pid + proc_start reads running, no reconciled key."""
    root = tmp_path
    _season(root, "s1", {"a1": _meta("a1", S124W2_PID, S124W2_START)})
    fake_proc.spawn(S124W2_PID, S124W2_START)
    snap = engine.read_status(root, "s1")["agents"]["a1"]
    assert snap["state"] == "running"
    assert "reconciled" not in snap


def test_pin7_exit_code_crash_takes_no_note(fake_proc, tmp_path):
    """The exit file is durable proof; an exit-code crash is not a /proc
    reconciliation and takes no note."""
    root = tmp_path
    _season(root, "s1", {"a1": _meta("a1", S124W2_PID, S124W2_START)})
    (root / "runs" / "s1" / "a1" / "exit").write_text("143\n", encoding="utf-8")
    snap = engine.read_status(root, "s1")["agents"]["a1"]
    assert snap["state"] == "crashed"
    assert snap["exit_code"] == 143
    assert "reconciled" not in snap


def test_pin8_terminated_marker_never_running(fake_proc, tmp_path):
    """The engine-authored terminated marker reads terminated."""
    root = tmp_path
    _season(root, "s1", {"a1": _meta("a1", S124W2_PID, S124W2_START)})
    (root / "runs" / "s1" / "a1" / "terminated").write_text(
        "terminated\n", encoding="utf-8"
    )
    snap = engine.read_status(root, "s1")["agents"]["a1"]
    assert snap["state"] == "terminated"
    assert "reconciled" not in snap
