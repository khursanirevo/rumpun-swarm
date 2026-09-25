"""s60 w2 pins — stall progress, specified before it exists.

Spec-first pins (red against current code) for the s60 contract (season
goal .rumpun/seasons/s60.yaml; w1 brief .rumpun/prompts/dev/
w1-stall-progress.md; ledger anchors 2026-09-16_s59-harvest and
2026-09-16_audit-40 — s59's w2 was killed mid-write by the stall watcher
while producing a 274-line pins file). Spec anchors, the measured red
set, and surface assumptions: .rumpun/runs/s60/w2/notes.md.

Contract these pins hold — every pin runs the real engine end to end
(`rumpun season start` as a bounded subprocess over a tmp .rumpun
project, the dual-start test's spawn pattern, a 0.1-minute stall
window):

1. A stub agent that only writes files — silent stdout, one small file
   per second — survives a stall window that kills it today: the season
   completes, the agent exits 0, and every marker file exists. Never
   stopped_stall.
2. A dead agent (no events at all: silent, writes nothing) still stalls:
   the season ends stopped_stall with the agent terminated by the stall
   rule, not the budget. Green pre-graft by design — the liveness guard
   the season must not weaken.
3. The stop record names the rule: a stopped_stall season's state.json
   carries a top-level "stall_stop" object — the rule text, the season's
   stall_s, and, per agent, which progress events counted (the source
   stamps under "sources"), the event counters, and the last-progress age
   ("last_progress_age_s", finite, >= stall_s for the dead fixture). The
   shape follows w1's landed record; the empty-sources map is the honest
   shape of a true stall.

Red history (measured, the runs are in notes.md): w1's engine change
landed in the shared tree before this file's first clean measurement, so
pins 1 and 2 measure green against the landed rule; pin 3 held the spec
open red on the record shape until re-pinned to the landed stall_stop
shape. The earlier runs (a wrong-reason lint refusal, then the shape
red) are in notes.md.

Grafting: drop this file into tests/ as-is. Helpers carry the _s60w2_
prefix, so nothing collides with existing defs. No pin touches the real
repo, ledger, or any live season: every fixture lives in pytest
tmp_path. Each run is bounded twice — S60W2_TIMEOUT on the watcher
subprocess and each benih's own 1-minute budget inside the engine — and
the dead stub self-exits at 91s, so a wedged engine ends the run itself
and the suite never hangs.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

S60W2_TIMEOUT = 120  # bounds one watcher subprocess; the budget bounds it harder
S60W2_STALL_MINUTES = 0.1  # the 6s stall window every pin exercises
S60W2_WRITES = 12  # the writer stub: one file per second, 12s, then exit 0
S60W2_SID = "s600"  # lint requires the s<N> id shape; s600 matches no real row

S60W2_SEASON = """\
id: s600
goal: "fixture"
metric: "m"
mode: fight
methodology:
  approach: "x"
  evidence: []
  primary_change:
    type: add
    node: execute
    baseline: "b"
    expected_band: "WIN if x"
    rollback: "git revert"
    eval_window: "s600"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
      reads: results.jsonl
benih:
  - name: w1
    route: {route}
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [all_exited, {{stall_minutes: 0.1}}]
"""


def _s60w2_root() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and in
    tests/ (post-graft): both sit under the repo root.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s60w2_proj(tmp_path: Path, route: str) -> tuple[Path, Path]:
    """One tmp project (.rumpun layout) and its season yaml, one benih.

    The named route is a stub: `writer` consumes the prompt, then echoes
    one small file per second into its workspace — silent stdout, agent.log
    stays 0 bytes — and exits 0; `dead` prints and writes nothing. The
    1-minute benih budget bounds any wedged watcher inside the engine
    itself.
    """
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    (root / "runs").mkdir()
    (root / "prompts" / "dev").mkdir(parents=True)
    writer = (
        "cat {prompt} > /dev/null; i=0;"
        f" while [ \"$i\" -lt {S60W2_WRITES} ]; do i=$((i+1));"
        " echo progress > \"s60w2_$i.md\"; sleep 1; done"
    )
    (root / "rumpun.yaml").write_text(
        "autonomy:\n"
        "  stage: manual\n"
        "  invariants: [goal_immutable, budget_cap, falsify_required]\n"
        "routes:\n"
        f"  writer: '{writer}'\n"
        "  dead: 'i=0; while [ \"$i\" -le 90 ]; do i=$((i+1)); sleep 1; done'\n",
        encoding="utf-8",
    )
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    season = root / "seasons" / "s60x.yaml"
    season.write_text(S60W2_SEASON.format(route=route), encoding="utf-8")
    return root, season


def _s60w2_start(tmp_path: Path, season: Path) -> subprocess.Popen[str]:
    """Launch the watcher CLI over the fixture; PYTHONPATH pins the repo src."""
    env = dict(os.environ)
    env["PYTHONPATH"] = (
        str(_s60w2_root() / "src") + os.pathsep + env.get("PYTHONPATH", "")
    )
    return subprocess.Popen(
        [sys.executable, "-m", "rumpun", "season", "start", str(season)],
        cwd=str(tmp_path), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )


def _s60w2_terminal(proc: subprocess.Popen[str], root: Path, sid: str) -> dict[str, Any]:
    """Bounded wait for any terminal status; the persisted state, read fresh.

    The watcher rewrites state.json atomically (tmp + replace), so a read
    is never torn; polling stops at the first terminal status.
    """
    state_path = root / "runs" / sid / "_season" / "state.json"

    def read_terminal() -> dict[str, Any] | None:
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return None if state.get("status") == "running" else state

    deadline = time.monotonic() + S60W2_TIMEOUT
    while time.monotonic() < deadline:
        state = read_terminal()
        if state is not None:
            return state
        if proc.poll() is not None:
            _out, err = proc.communicate(timeout=30)
            raise AssertionError(
                f"watcher exited before a terminal state (rc={proc.returncode});"
                f" stderr:\n{err}"
            )
        time.sleep(0.05)
    raise AssertionError(
        f"season {sid} never reached a terminal state in {S60W2_TIMEOUT}s"
    )


def _s60w2_finish(proc: subprocess.Popen[str]) -> tuple[int, str]:
    """Drain the watcher subprocess, bounded; (returncode, stderr tail)."""
    try:
        _out, err = proc.communicate(timeout=S60W2_TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise
    return proc.returncode, err


# --- pin 1: the s59 kill becomes impossible ------------------------------------


def test_s60w2_file_writer_survives_the_stall_window(tmp_path: Path) -> None:
    """A silent file-writing stub completes a window that kills it today.

    The stub appends nothing to agent.log (0 bytes throughout: no stdout,
    no stderr), writes one marker file per second, and exits 0 at 12s —
    past the 6s window. The pre-s60 rule saw no stream growth and stopped the
    season stopped_stall at ~7s (s59's w2 died exactly so); the spec rule
    counts the file writes: the season completes, the agent exits 0, and
    all 12 markers exist — the writes really happened while alive.
    """
    root, season = _s60w2_proj(tmp_path, "writer")
    proc = _s60w2_start(tmp_path, season)
    state = _s60w2_terminal(proc, root, S60W2_SID)
    rc, err = _s60w2_finish(proc)
    assert state["status"] == "completed", (
        f"season ended {state['status']}, not completed; stderr:\n{err}"
    )
    agent = (state.get("agents") or {}).get("w1") or {}
    assert agent.get("state") == "exited", f"agent snap: {agent}"
    assert agent.get("exit_code") == 0, f"agent snap: {agent}"
    ws = root / "runs" / S60W2_SID / "w1"
    written = [n for n in range(1, S60W2_WRITES + 1) if (ws / f"s60w2_{n}.md").is_file()]
    assert len(written) == S60W2_WRITES, (
        f"marker files missing (the stub died at {len(written)}): {written}"
    )
    log = root / "runs" / S60W2_SID / "w1" / "agent.log"
    assert log.is_file() and log.stat().st_size == 0, "stub must hold no stream events"
    assert rc == 0, f"season start exit {rc}:\n{err}"


# --- pin 2: the liveness guard --------------------------------------------------


def test_s60w2_dead_stub_still_stalls(tmp_path: Path) -> None:
    """A dead agent (no events at all) still stalls — the rule counts progress.

    The stub prints nothing, writes nothing, sleeps 91s. The stall rule
    must still fire at the 6s window: stopped_stall, the agent terminated
    by the stall (no terminated_budget key — the 60s budget never fired),
    agent.log 0 bytes (no events of any kind existed). Green pre-graft by
    design; whatever the merge lands must keep it green.
    """
    root, season = _s60w2_proj(tmp_path, "dead")
    proc = _s60w2_start(tmp_path, season)
    state = _s60w2_terminal(proc, root, S60W2_SID)
    _rc, err = _s60w2_finish(proc)
    assert state["status"] == "stopped_stall", (
        f"season ended {state['status']}; stderr:\n{err}"
    )
    agent = (state.get("agents") or {}).get("w1") or {}
    assert agent.get("state") == "terminated", f"agent snap: {agent}"
    assert not agent.get("terminated_budget"), f"budget fired first; snap: {agent}"
    log = root / "runs" / S60W2_SID / "w1" / "agent.log"
    assert log.is_file() and log.stat().st_size == 0, "dead stub must hold no events"


# --- pin 3: the stop record names the rule --------------------------------------


def test_s60w2_stop_record_names_the_rule(tmp_path: Path) -> None:
    """A stopped_stall record carries the counted classes and the age.

    Same dead-stub fixture, the record side: the persisted state.json must
    carry a top-level "stall_stop" object (the landed s60 w1 shape) — the
    rule text, the season's stall_s, and per-agent evidence. For the dead
    agent: sources == {} (no last_progress, last_tool_use, or
    last_ws_progress stamp exists — no event of any class counted),
    tool_use_count is None, ws_bytes an int (the recorded baseline; growth
    would have stamped a source), and a finite last_progress_age_s >= the
    season's stall_s.
    """
    root, season = _s60w2_proj(tmp_path, "dead")
    proc = _s60w2_start(tmp_path, season)
    state = _s60w2_terminal(proc, root, S60W2_SID)
    _rc, err = _s60w2_finish(proc)
    assert state["status"] == "stopped_stall", (
        f"season ended {state['status']}; stderr:\n{err}"
    )
    record = state.get("stall_stop")
    assert isinstance(record, dict), (
        f"stop record carries no rule; state keys: {sorted(state)}"
    )
    assert isinstance(record.get("rule"), str) and record["rule"], (
        f"stop record must name the rule: {record}"
    )
    assert float(record.get("stall_s", -1.0)) == float(state.get("stall_s", -2.0)), (
        f"stop record stall_s must match the season: {record}"
    )
    agent = (record.get("agents") or {}).get("w1") or {}
    age = agent.get("last_progress_age_s")
    assert isinstance(age, (int, float)) and not isinstance(age, bool), (
        f"last_progress_age_s must be a number: {agent}"
    )
    window = float(state.get("stall_s", 0.0))
    assert math.isfinite(float(age)) and float(age) >= window, (
        f"last-progress age {age} must be >= the stall window {window}: {agent}"
    )
    assert agent.get("sources") == {}, (
        f"a dead agent counted no event of any class: {agent}"
    )
    assert agent.get("tool_use_count") is None, (
        f"no tool_use event ever parsed for a dead agent: {agent}"
    )
    assert isinstance(agent.get("ws_bytes"), int), (
        f"the watched-bytes scan ran (baseline recorded): {agent}"
    )
