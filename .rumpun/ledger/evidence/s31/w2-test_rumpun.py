"""Tests for the rumpun core modules: engine internals, akar records, harvest,
evolve draft/apply, lint findings, report rendering, and the collab lane.

Everything runs on tmp_path fixtures: no network, no repo state, no skips.
The collab tests are spec-first: rumpun.collab lands at integration (w1's
lane module) with the ratified contract — prepare_lane creates the lane/lock
pair without truncating, append_event writes one JSON line under flock with
seq = existing line count, read_events replays in file order and raises
LaneError on a corrupt line.

test_dual_start_single_spawner (s6, w2) closes the state-lock story at
process level: two concurrent `python -m rumpun season start` subprocesses
on one season serialize on _season/state.lock — the second starter blocks,
then reattaches to the first's agents instead of double-spawning them.

The evolve rollback tests are spec-first (s9, w2): rollback_season lands at
integration (w1's evolve module) under the ratified contract — sid must
match s<N>, musim/<sid>.yaml must exist (a missing file hints to use
reject), the season moves to musim/rejected/<sid>.yaml with the directory
created and collisions refused, akar record rollback-<sid> carries
"rollback_to_last_good" and "git revert", and akar.AkarError wraps into
EvolveError.

The audit tests are spec-first (s11, w2): rumpun.audit lands at
integration (w1's audit module) under the ratified contract — run_audit
reads the last n musim seasons by number plus their rimba/ artifacts,
appends the akar record audit-<k> (k = 1 + count of audit-* files in
akar/) and returns its path; the body carries per-phase liveness lines
"wrote its artifact in K of N" over the scanned seasons, a dead-phase
finding that names the phase and cites the season id, an "exercise or
trim" candidate when a declared phase has 0 artifacts across >= 2 scanned
seasons, a stall recurrence finding per stopped_stall season with a
"re-size stall/budget" candidate at >= 2, akar duplicate-id errors wrapped
into AuditError, and musim/ and rimba/ left byte-identical.

The audit-extension tests are spec-first (s13, w2): the extension lands at
integration under the ratified contract — for each route over the audited
engine seasons a line "route R: A clean-deliverable, B clean-empty, C
failed, D not-exited over N spawns" citing the seasons that spawned it
(deliverable = any non-bookkeeping file in the agent workspace, scanned
recursively; bookkeeping = agent.log, exit, prompt.md, prompt-meta.yaml,
state.json, terminated, terminated.tmp, __pycache__; exit 0 + deliverable
= clean-deliverable, exit 0 without = clean-empty, non-zero exit =
failed, any other state = not-exited), a "tool-check" candidate when one
route has >= 2 clean-empty spawns, "band masked value" findings for
harvested LOSS seasons (akar <sid>-harvest record) holding a results.jsonl
row "integrated": true with a "recalibrate LOSS bands" candidate at >= 2,
a "campaign_cost_cap unset" finding when rumpun.yaml lacks
budget.campaign_cost_cap (finding only, never a candidate),
candidate priority phase -> route -> calibration under MAX_CANDIDATES = 3,
and musim/ plus rimba/ still byte-identical after run_audit.

The stream tool-evidence tests are spec-first (s16, w2): the parser lands
at integration (w1's engine patch) under the ratified contract --
stream_tool_names parses line-delimited JSON, splitting on newline only so
a raw U+2028 inside a JSON string is not a line break, skips malformed
lines with one DEBUG log each, and collects tool names from tool_use
blocks; file_tools marks sticky true on the first file-tool event;
ToolSearch/WebFetch/Task/Agent never mark; false is set only at finalize
with >= 1 parseable event and zero file-tool events; the key stays absent
when the stream held zero parseable events; stream_offset advances
additively and a scan over unchanged bytes re-classifies nothing;
truncated real s15 streams replay to file_tools true for both writers;
file_tools and stream_offset are additive keys (report bytes and audit F4
counts unchanged); scanning rides the existing watch cycle, no new
polling.
"""

import fcntl
import hashlib
import inspect
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
import yaml

from rumpun import akar, engine, evolve, harvest, lint, report
from rumpun import audit as audit_mod
from rumpun import cli as cli_mod

# isort: split
from rumpun import audit, collab  # spec-first: modules land at integration

# isort: split
from rumpun import routes, scaffold  # spec-first: M11 pin (codex-review-2026-09-14)

# isort: split
from rumpun import yamlio  # spec-first: M9 pins (codex-review-2026-09-14)

# isort: split
from rumpun import cli  # spec-first: s24 pins (harvest --band/--observed pass-through)

RUMPUN_YAML = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "cat {prompt} | true"
"""

# s6 dual-start fixture: the route is a real command that exits 0 in
# milliseconds, so both starters and both agents finish fast.
RUMPUN_YAML_DUAL = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "cat {prompt} > /dev/null"
"""

# s13 w2 budget-finding fixture: the cost cap present at the ratified path.
RUMPUN_YAML_CAPPED = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
budget:
  campaign_cost_cap: 100
routes:
  glm: "cat {prompt} | true"
"""

SEASON_S1 = """\
id: s1
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
    eval_window: "s1"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
benih:
  - name: w1
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 1}
stop:
  "on": [all_exited]
"""

# Same shape as SEASON_S1 but with two benih, so "each name exactly once"
# in the spawned map has real content to check against.
SEASON_DUAL = """\
id: s1
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
    eval_window: "s1"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
benih:
  - name: alpha
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 1}
  - name: beta
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 1}
stop:
  "on": [all_exited]
"""


def _write_proj(tmp_path, season_text, season_name="s1.yaml", project_yaml=RUMPUN_YAML):
    """Build <tmp>/proj/.rumpun: rumpun.yaml, one season, the dummy prompt."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "musim").mkdir(parents=True)
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(project_yaml, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    season = root / "musim" / season_name
    season.write_text(season_text, encoding="utf-8")
    return root, season


def _agent_ws(tmp_path):
    """One agent workspace whose state.json proc_start never matches a live pid."""
    ws = tmp_path / "a"
    ws.mkdir()
    (ws / "state.json").write_text(
        json.dumps(
            {
                "name": "a",
                "route": "glm",
                "cmd": "x",
                "pid": 1,
                "proc_start": 987654321,
                "started_at": 0.0,
            }
        ),
        encoding="utf-8",
    )
    return ws


# --- engine -------------------------------------------------------------------


def test_proc_start_ticks_no_proc_entry():
    assert engine._proc_start_ticks(4194303) is None


def test_stop_rules_stall_and_budget_seconds():
    season = {
        "stop": {"on": ["all_exited", {"stall_minutes": 15}]},
        "benih": [{"name": "w1", "budget": {"minutes": 20}}],
    }
    assert engine._stop_rules(season) == (900.0, 1200.0)


@pytest.mark.parametrize(
    ("exit_text", "expected_state", "expected_code"),
    [("0", "exited", 0), ("3", "failed", 3)],
)
def test_agent_snap_exit_file(tmp_path, exit_text, expected_state, expected_code):
    ws = _agent_ws(tmp_path)
    (ws / "exit").write_text(exit_text, encoding="utf-8")
    snap = engine._agent_snap(ws, stall_s=900.0)
    assert snap["state"] == expected_state
    assert snap["exit_code"] == expected_code
    assert snap["name"] == "a"
    assert snap["route"] == "glm"


def test_agent_snap_no_exit_file_crashed(tmp_path):
    ws = _agent_ws(tmp_path)
    snap = engine._agent_snap(ws, stall_s=900.0)
    assert snap["state"] == "crashed"
    assert snap["exit_code"] is None


# --- akar ---------------------------------------------------------------------


def test_akar_append_record_layout_and_duplicate(tmp_path):
    path = akar.append_record(tmp_path, "rec-1", "title one", "body text")
    assert path.parent == tmp_path / "akar"
    assert path.name.endswith("_rec-1.md")
    text = path.read_text(encoding="utf-8")
    assert "id: rec-1" in text
    assert "title: title one" in text
    assert "body text" in text
    digest = hashlib.sha256(b"body text").hexdigest()
    assert f"sha256: {digest}" in text
    with pytest.raises(akar.AkarError):
        akar.append_record(tmp_path, "rec-1", "second try", "other body")


# --- harvest ------------------------------------------------------------------


def _write_season_state(tmp_path):
    """Completed season state for s1, as engine._finalize would leave it."""
    state_dir = tmp_path / "rimba" / "s1" / "_season"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text(
        json.dumps(
            {
                "id": "s1",
                "status": "completed",
                "started_at": 1.0,
                "ended_at": 2.0,
                "agents": {
                    "w1": {
                        "name": "w1",
                        "route": "glm",
                        "state": "exited",
                        "exit_code": 0,
                        "seconds": 1.0,
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def test_harvest_season_records_verdict(tmp_path):
    _write_season_state(tmp_path)
    path = harvest.harvest_season(tmp_path, "s1", "WIN", "note")
    text = path.read_text(encoding="utf-8")
    assert "verdict: WIN" in text
    assert "implies: note" in text


def test_harvest_season_rejects_unknown_verdict(tmp_path):
    with pytest.raises(ValueError, match="verdict must be"):
        harvest.harvest_season(tmp_path, "s1", "MAYBE", "note")


# --- evolve -------------------------------------------------------------------


def test_evolve_draft_next_empties_primary_change(tmp_path):
    root, parent = _write_proj(tmp_path, SEASON_S1)
    drafted = evolve.draft_next(root, parent)
    assert drafted == root / "musim" / "s2.yaml"
    draft = yaml.safe_load(drafted.read_text(encoding="utf-8"))
    assert draft["id"] == "s2"
    assert draft["parent"] == "s1"
    change = draft["methodology"]["primary_change"]
    for field in ("baseline", "expected_band", "rollback", "eval_window"):
        assert change[field] == ""


def test_evolve_apply_blocks_unfilled_draft(tmp_path):
    root, parent = _write_proj(tmp_path, SEASON_S1)
    drafted = evolve.draft_next(root, parent)
    with pytest.raises(evolve.EvolveError, match="baseline"):
        evolve.apply(root, drafted)


# --- lint ---------------------------------------------------------------------


def test_lint_empty_baseline_is_error(tmp_path):
    season_text = SEASON_S1.replace("id: s1\n", "id: s2\nparent: s1\n").replace(
        '    baseline: "b"', '    baseline: ""'
    )
    _root, season = _write_proj(tmp_path, season_text, season_name="s2.yaml")
    findings = lint.lint(season)
    assert any(f.severity == "error" and "baseline" in f.message for f in findings)


# --- collab (spec-first) --------------------------------------------------------


def test_collab_lane_two_events_seq_and_senders(tmp_path):
    lane = collab.prepare_lane(tmp_path, "s1", "dev")
    assert Path(lane["file"]).is_file()
    assert Path(lane["lock"]).is_file()
    first = collab.append_event(lane, "w1", {"text": "first"})
    second = collab.append_event(lane, "w2", {"text": "second"})
    assert first["seq"] == 0
    assert second["seq"] == 1
    events = collab.read_events(lane)
    assert [(e["seq"], e["from"]) for e in events] == [(0, "w1"), (1, "w2")]
    assert events[0]["text"] == "first"
    assert events[1]["text"] == "second"


def test_collab_prepare_lane_never_truncates(tmp_path):
    lane = collab.prepare_lane(tmp_path, "s1", "dev")
    collab.append_event(lane, "w1", {"text": "keep"})
    again = collab.prepare_lane(tmp_path, "s1", "dev")
    assert again["file"] == lane["file"]
    assert len(collab.read_events(again)) == 1


def test_collab_read_events_corrupt_line(tmp_path):
    lane = collab.prepare_lane(tmp_path, "s1", "dev")
    collab.append_event(lane, "w1", {"text": "ok"})
    with Path(lane["file"]).open("a", encoding="utf-8") as fh:
        fh.write("this line is not json\n")
    with pytest.raises(collab.LaneError):
        collab.read_events(lane)


# --- report ---------------------------------------------------------------------


def test_report_document_provenance_and_determinism():
    status = {
        "id": "s1",
        "status": "completed",
        "started_at": 1.0,
        "ended_at": 2.0,
        "agents": {
            "w1": {
                "name": "w1",
                "route": "glm",
                "state": "exited",
                "exit_code": 0,
                "seconds": 1.0,
            }
        },
    }
    doc = report._document(status)
    assert "s1" in doc
    for label in ("[H]", "[A]", "[D]"):
        assert label in doc
    assert report._document(status) == doc


# --- terminated marker (defect from s2, spec by s4 w1) ------------------------


def test_agent_snap_terminated_marker(tmp_path):
    ws = _agent_ws(tmp_path)
    (ws / "terminated").write_text("terminated\n", encoding="utf-8")
    snap = engine._agent_snap(ws, stall_s=900.0)
    assert snap["state"] == "terminated"
    assert snap["exit_code"] is None


def test_agent_snap_exit_file_beats_marker(tmp_path):
    ws = _agent_ws(tmp_path)
    (ws / "terminated").write_text("terminated\n", encoding="utf-8")
    (ws / "exit").write_text("0", encoding="utf-8")
    assert engine._agent_snap(ws, stall_s=900.0)["state"] == "exited"
    (ws / "exit").write_text("3", encoding="utf-8")
    assert engine._agent_snap(ws, stall_s=900.0)["state"] == "failed"


# --- lane concurrency (w2 s4 scope, harness-applied) --------------------------


def test_collab_append_event_concurrent_dense_seq(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    lane = collab.prepare_lane(tmp_path, "s1", "dev")

    def burst(k):
        for i in range(25):
            collab.append_event(lane, f"w{k}", {"i": i})

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(burst, range(4)))
    seqs = [e["seq"] for e in collab.read_events(lane)]
    assert seqs == list(range(100))


# --- state lock (w1 s5 scope; concurrency test harness-applied) ---------------


def test_save_state_lock_serializes_concurrent_writers(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    root = tmp_path
    (root / "rimba" / "s1" / "_season").mkdir(parents=True)

    def write(k):
        for i in range(10):
            engine._save_state(root, "s1", {"n": k * 10 + i})

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write, range(4)))
    state = engine._load_state(root, "s1")
    assert isinstance(state.get("n"), int)
    assert (root / "rimba" / "s1" / "_season" / "state.lock").is_file()


# --- dual start at process level (w2 s6 scope) --------------------------------


# s21 L2 (codex-review-2026-09-14): the old test launched both starters
# back-to-back, so starter 2's contention was luck. When it read the season
# after starter 1 had already finalized, the finished check raised and it
# exited nonzero (~1/5 loaded runs, 5+ transients). The race is closed with
# an explicit barrier: a marker-gated route keeps the season provably
# un-finalizable while the test orders the starters, and the agents are
# released only after starter 2 is observed contending on state.lock and
# then observed clear of the spawn transaction.
DUAL_BARRIER_ROUTE = (
    "while [ ! -f {marker} ]; do sleep 0.5; done; cat {prompt} > /dev/null"
)


def _wait_until(action, timeout, message):
    """Poll action() every 20ms; return the first truthy value, else fail."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = action()
        if value:
            return value
        time.sleep(0.02)
    pytest.fail(f"{message} (waited {timeout}s)")


def _pid_has_fd(pid: int, target: Path) -> bool:
    """True while /proc/<pid>/fd exposes an fd resolving to `target`."""
    try:
        entries = os.listdir(f"/proc/{pid}/fd")
    except OSError:
        return False
    resolved = str(os.path.realpath(target))
    for fd in entries:
        try:
            if os.path.realpath(f"/proc/{pid}/fd/{fd}") == resolved:
                return True
        except OSError:
            continue
    return False


def test_dual_start_single_spawner(tmp_path):
    """Two concurrent `rumpun season start` processes spawn each agent once.

    The barrier, in order: the route blocks each agent on a marker file, so
    starter 1 cannot finalize while the test withholds the marker. Starter 1
    launches alone; the test waits until the flock-serialized spawn
    transaction has persisted both agent pids, then takes _season/state.lock
    itself. Starter 2 launches against that held lock and is observed via
    /proc/<pid>/fd blocked with the lock fd open: demonstrably contending,
    its spawned-alphas line not yet emitted. The test releases the lock,
    observes starter 2 acquire it, pass the finished check against a season
    provably still running, and leave the transaction (lock fd closed).
    Only then does the marker touch release the agents; both watchers
    finalize (first writer wins, the second returns cleanly via
    engine._finalize) and both exit 0.

    Proven by: both exit 0, the season reaches exactly one terminal
    state.json with status completed, each benih name appears in the spawned
    map exactly once, both per-agent workspaces hold a state.json, and the
    "spawned alpha" log line appears in exactly one of the two stderr
    streams.
    """
    marker = tmp_path / "agents_go"
    project_yaml = RUMPUN_YAML_DUAL.replace(
        "cat {prompt} > /dev/null",
        DUAL_BARRIER_ROUTE.replace("{marker}", marker.as_posix()),
    )
    root, season = _write_proj(tmp_path, SEASON_DUAL, project_yaml=project_yaml)
    cmd = [sys.executable, "-m", "rumpun", "season", "start", str(season)]

    # Starter 1 launches alone. Its spawn transaction persists both agent
    # pids under the flock; with the marker absent the season stays running,
    # so this wait does not depend on scheduler timing.
    starter1 = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        cwd=str(tmp_path),
    )
    season_state = root / "rimba" / "s1" / "_season" / "state.json"
    lock_path = root / "rimba" / "s1" / "_season" / "state.lock"

    def both_spawned():
        if starter1.poll() is not None:
            _out, err = starter1.communicate(timeout=30)
            pytest.fail(f"starter 1 exited before spawning both; stderr:\n{err}")
        try:
            state = json.loads(season_state.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        spawned = state.get("spawned") or {}
        return all(
            (spawned.get(name) or {}).get("pid") is not None
            for name in ("alpha", "beta")
        )

    _wait_until(both_spawned, 30, "starter 1 never persisted both agent pids")

    # The test now holds state.lock: starter 2 must queue on it, not on luck.
    with open(lock_path, "a") as probe:
        deadline = time.monotonic() + 5
        while True:
            try:
                fcntl.flock(probe.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > deadline:
                    pytest.fail(
                        "state.lock held by an unexpected holder after 5s"
                    )
                time.sleep(0.02)

        starter2 = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            cwd=str(tmp_path),
        )

        def contending():
            if starter2.poll() is not None:
                _out, err = starter2.communicate(timeout=30)
                msg = f"starter 2 exited before contending on the lock; stderr:\n{err}"
                pytest.fail(msg)
            return _pid_has_fd(starter2.pid, lock_path)

        _wait_until(contending, 30, "starter 2 never showed the lock fd open")

    # Probe released: starter 2 acquires the lock, its finished check reads a
    # season provably still running (marker absent), it reattaches and exits
    # the transaction -- observed as the lock fd closing while it stays alive.
    def past_transaction():
        return (
            not _pid_has_fd(starter2.pid, lock_path)
            and starter2.poll() is None
        )

    _wait_until(
        past_transaction, 30,
        "starter 2 never cleared the spawn-transaction lock",
    )

    # Starter 2 has passed its finished check; the agents may now exit and
    # both watchers finalize.
    marker.touch()
    starters = [starter1, starter2]
    results = []
    for starter in starters:
        try:
            results.append(starter.communicate(timeout=180))
        except subprocess.TimeoutExpired:
            starter.kill()
            out, err = starter.communicate()
            pytest.fail(f"season start did not finish in 180s; stdout={out} stderr={err}")
    for starter, (_out, err) in zip(starters, results, strict=True):
        assert starter.returncode == 0, f"starter exited badly; stderr: {err}"
    spawn_logs = sum(err.count("spawned alpha") for _out, err in results)
    assert spawn_logs == 1, "alpha was spawned twice: state.lock did not serialize"
    final = root / "rimba" / "s1" / "_season" / "state.json"
    state = json.loads(final.read_text(encoding="utf-8"))
    assert state["status"] == "completed"
    spawned = list(state["spawned"])
    assert spawned.count("alpha") == 1
    assert spawned.count("beta") == 1
    assert len(spawned) == 2
    for name in ("alpha", "beta"):
        assert (root / "rimba" / "s1" / name / "state.json").is_file()


def test_collab_append_event_first_use_creates_files(tmp_path):
    lane = {
        "file": str(tmp_path / "fresh" / "lane-x.jsonl"),
        "lock": str(tmp_path / "fresh" / "lane-x.lock"),
    }
    event = collab.append_event(lane, "operator", {"text": "hi"})
    assert event["seq"] == 0
    assert len(collab.read_events(lane)) == 1


# --- evolve approve/reject (w2 s8 scope, harness-applied) ---------------------


def test_approve_draft_records_and_keeps_draft(tmp_path):
    root, drafted = _write_proj(tmp_path, SEASON_S1)
    record = evolve.approve_draft(root, drafted)
    text = record.read_text(encoding="utf-8")
    assert "approve-s1" in text
    assert "fixture" in text  # the goal line
    assert drafted.read_text(encoding="utf-8") == SEASON_S1  # draft untouched


def test_approve_draft_bad_input_raises(tmp_path):
    root, _drafted = _write_proj(tmp_path, SEASON_S1)
    with pytest.raises(evolve.EvolveError):
        evolve.approve_draft(root, root / "musim" / "missing.yaml")
    bad = root / "musim" / "bad.yaml"
    bad.write_text("id: nope\n", encoding="utf-8")
    with pytest.raises(evolve.EvolveError):
        evolve.approve_draft(root, bad)


def test_reject_draft_moves_and_records(tmp_path):
    root, drafted = _write_proj(tmp_path, SEASON_S1)
    record = evolve.reject_draft(root, drafted)
    assert not drafted.exists()
    moved = root / "musim" / "rejected" / "s1.yaml"
    assert moved.is_file()
    text = record.read_text(encoding="utf-8")
    assert "reject-s1" in text
    assert "rollback_to_last_good" in text
    with pytest.raises(evolve.EvolveError):
        evolve.reject_draft(root, moved.parent.parent / "s1.yaml")


# --- evolve rollback (w2 s9 scope, spec-first) ---------------------------------


def test_rollback_season_moves_and_records(tmp_path):
    root, season = _write_proj(tmp_path, SEASON_S1)
    record = evolve.rollback_season(root, "s1")
    assert not season.exists()
    moved = root / "musim" / "rejected" / "s1.yaml"
    assert moved.is_file()
    assert moved.read_text(encoding="utf-8") == SEASON_S1
    assert record.parent == root / "akar"  # the return is the akar record
    text = record.read_text(encoding="utf-8")
    assert "rollback-s1" in text
    assert "rollback_to_last_good" in text
    assert "git revert" in text


def test_rollback_season_missing_raises(tmp_path):
    root, _season = _write_proj(tmp_path, SEASON_S1)
    with pytest.raises(evolve.EvolveError, match="reject"):
        evolve.rollback_season(root, "s2")


@pytest.mark.parametrize("sid", ["x9", "season1"])
def test_rollback_season_bad_sid_raises(tmp_path, sid):
    root, _season = _write_proj(tmp_path, SEASON_S1)
    with pytest.raises(evolve.EvolveError):
        evolve.rollback_season(root, sid)


def test_rollback_season_twice_raises(tmp_path):
    root, _season = _write_proj(tmp_path, SEASON_S1)
    evolve.rollback_season(root, "s1")
    with pytest.raises(evolve.EvolveError):
        evolve.rollback_season(root, "s1")


def test_rollback_season_collision_raises(tmp_path):
    root, season = _write_proj(tmp_path, SEASON_S1)
    squatter = root / "musim" / "rejected" / "s1.yaml"
    squatter.parent.mkdir(parents=True)
    squatter.write_text("already here\n", encoding="utf-8")
    with pytest.raises(evolve.EvolveError):
        evolve.rollback_season(root, "s1")
    assert season.exists()  # a refused collision must not destroy either file


def test_rollback_season_akar_error_wraps(tmp_path):
    root, _season = _write_proj(tmp_path, SEASON_S1)
    akar.append_record(root, "rollback-s1", "pre-existing record", "occupies the id")
    with pytest.raises(evolve.EvolveError):
        evolve.rollback_season(root, "s1")


# --- audit reflection (w2 s11 scope, spec-first) ---------------------------------


AUDIT_SEASON = """\
id: {sid}
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
    eval_window: "{sid}"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
    - phase: evaluate
      primitive: evaluate
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: verdicts.jsonl
benih:
  - name: w1
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [all_exited]
"""


def _write_audit_proj(tmp_path, sids=("s1", "s2"), project_yaml=RUMPUN_YAML):
    """Audit fixture root: given rumpun.yaml, N seasons, empty akar/."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "musim").mkdir(parents=True)
    (root / "akar").mkdir()
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(project_yaml, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    for sid in sids:
        (root / "musim" / f"{sid}.yaml").write_text(
            AUDIT_SEASON.format(sid=sid), encoding="utf-8"
        )
    return root


def _write_rimba_season(root, sid, status="completed", artifacts=True):
    """One rimba/<sid>: both pipeline artifacts plus _season/state.json."""
    season = root / "rimba" / sid
    season.mkdir(parents=True)
    if artifacts:
        (season / "results.jsonl").write_text('{"n": 1}\n', encoding="utf-8")
        (season / "verdicts.jsonl").write_text('{"v": "WIN"}\n', encoding="utf-8")
    state = season / "_season"
    state.mkdir()
    (state / "state.json").write_text(
        json.dumps({"id": sid, "status": status, "started_at": 1.0, "ended_at": 2.0}),
        encoding="utf-8",
    )
    return season


def _write_spawn(root, sid, name, route, outcome):
    """One agent workspace rimba/<sid>/<name>/ shaped to land in `outcome`.

    outcome is one of clean-deliverable, clean-empty, failed, not-exited
    (terminated marker, no exit file), or crashed (no exit file at all);
    not-exited and crashed are both the spec's "other state" class. The
    __pycache__/mod.pyc and terminated.tmp noise on clean-empty and the
    nested results/findings.md on clean-deliverable pin the recursive
    non-bookkeeping scan: the pyc must not count as a deliverable, the
    nested file must.
    """
    ws = root / "rimba" / sid / name
    ws.mkdir(parents=True)
    for book in ("agent.log", "prompt.md", "prompt-meta.yaml"):
        (ws / book).write_text("book\n", encoding="utf-8")
    (ws / "state.json").write_text(
        json.dumps(
            {
                "name": name,
                "route": route,
                "cmd": "x",
                "pid": 1,
                "proc_start": 987654321,
                "started_at": 0.0,
            }
        ),
        encoding="utf-8",
    )
    # The engine publishes the finalized snap into the season-level
    # _season/state.json agents block; mirror that so the audit's route
    # scan sees the spawn (fields the classifier reads: route, state,
    # exit_code).
    season_state_path = root / "rimba" / sid / "_season" / "state.json"
    season_state = json.loads(season_state_path.read_text(encoding="utf-8"))
    snap: dict = {"route": route}
    if outcome.startswith("clean"):
        snap.update(state="exited", exit_code=0)
    elif outcome == "failed":
        snap.update(state="failed", exit_code=3)
    elif outcome == "not-exited":
        snap.update(state="terminated")
    else:  # crashed: no exit file, no marker
        snap.update(state="crashed")
    season_state.setdefault("agents", {})[name] = snap
    season_state_path.write_text(json.dumps(season_state), encoding="utf-8")
    if outcome == "not-exited":
        (ws / "terminated").write_text("terminated\n", encoding="utf-8")
    elif outcome != "crashed":
        code = "0" if outcome.startswith("clean") else "3"
        (ws / "exit").write_text(code, encoding="utf-8")
    if outcome == "clean-deliverable":
        nested = ws / "results" / "findings.md"
        nested.parent.mkdir()
        nested.write_text("payload\n", encoding="utf-8")
    if outcome == "clean-empty":
        cache = ws / "__pycache__"
        cache.mkdir()
        (cache / "mod.cpython-310.pyc").write_bytes(b"\x00")
        (ws / "terminated.tmp").write_text("term\n", encoding="utf-8")
    return ws


def _write_results_rows(root, sid, rows):
    """Overwrite rimba/<sid>/results.jsonl with the given row dicts."""
    path = root / "rimba" / sid / "results.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def _write_harvest_record(root, sid, verdict):
    """A season-level verdicts.jsonl row — the verdict rule the audit reads."""
    path = root / "rimba" / sid / "verdicts.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "season": sid,
        "verdict": verdict,
        "metric": "modules_integrated",
        "implies": "fixture",
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    return path


def _audit_base(tmp_path):
    """Base audit fixture: s1 completed with both artifacts, rimba/s2 empty."""
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")
    (root / "rimba" / "s2").mkdir(parents=True)
    return root


def _tree_snapshot(root, sub):
    """Map every file under root/<sub> to its bytes; {} when the dir is absent."""
    base = root / sub
    if not base.is_dir():
        return {}
    return {
        str(p.relative_to(base)): p.read_bytes()
        for p in sorted(base.rglob("*"))
        if p.is_file()
    }


def test_run_audit_first_record_is_audit_1(tmp_path):
    root = _audit_base(tmp_path)
    record = audit.run_audit(root)
    assert record.parent == root / "akar"
    assert "audit-1" in record.name
    assert "audit-1" in record.read_text(encoding="utf-8")


def test_run_audit_second_run_writes_audit_2(tmp_path):
    root = _audit_base(tmp_path)
    first = audit.run_audit(root)
    second = audit.run_audit(root)
    assert "audit-2" in second.name
    assert "audit-2" in second.read_text(encoding="utf-8")
    assert first.is_file()  # append-only: the earlier record survives


def test_run_audit_dead_phase_names_phase_and_season(tmp_path):
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")  # no rimba/s2 dir at all
    text = audit.run_audit(root).read_text(encoding="utf-8")
    lines = text.splitlines()
    for phase in ("execute", "evaluate"):
        assert any(phase in line and "s2" in line for line in lines)


def test_run_audit_liveness_line_and_alive_negative(tmp_path):
    root = _audit_base(tmp_path)
    text = audit.run_audit(root).read_text(encoding="utf-8")
    assert "wrote its artifact in 1 of 2" in text
    assert "exercise or trim" not in text  # 1 of 2 is liveness, not death


def test_run_audit_zero_artifacts_yield_exercise_or_trim(tmp_path):
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1", artifacts=False)  # state.json only
    (root / "rimba" / "s2").mkdir(parents=True)
    text = audit.run_audit(root).read_text(encoding="utf-8")
    assert any(
        "exercise or trim" in line and "execute" in line for line in text.splitlines()
    )


def test_run_audit_single_stall_finding_no_resize(tmp_path):
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2", status="stopped_stall")
    text = audit.run_audit(root).read_text(encoding="utf-8")
    assert "s2" in text and "stall" in text  # the recurrence finding
    assert "re-size" not in text  # one stall is a finding, not a candidate


def test_run_audit_two_stalls_yield_resize_candidate(tmp_path):
    root = _write_audit_proj(tmp_path, sids=("s1", "s2", "s3"))
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2", status="stopped_stall")
    _write_rimba_season(root, "s3", status="stopped_stall")
    text = audit.run_audit(root).read_text(encoding="utf-8")
    assert "re-size" in text


def test_run_audit_never_modifies_musim_or_rimba(tmp_path):
    root = _audit_base(tmp_path)
    before = {sub: _tree_snapshot(root, sub) for sub in ("musim", "rimba")}
    audit.run_audit(root)
    after = {sub: _tree_snapshot(root, sub) for sub in ("musim", "rimba")}
    assert before == after


def test_run_audit_last_n_takes_highest_season_numbers(tmp_path):
    root = _write_audit_proj(tmp_path)  # musim holds s1 and s2
    _write_rimba_season(root, "s2")  # only s2 has a rimba dir
    text = audit.run_audit(root, last_n=1).read_text(encoding="utf-8")
    assert "s1" not in text  # the window is the highest-numbered season only
    # s2 (not s1) was scanned: it wrote both artifacts, s1 has no rimba dir,
    # so a wrong window would read "0 of 1" with findings citing s1.
    assert "wrote its artifact in 1 of 1" in text


def test_run_audit_duplicate_id_wraps_into_audit_error(tmp_path):
    root = _audit_base(tmp_path)
    # occupied.md declares audit-1 without being an audit-* file, so the
    # next index stays 1 and akar raises the duplicate-id error to wrap.
    (root / "akar" / "occupied.md").write_text(
        "# akar record: audit-1\nid: audit-1\n", encoding="utf-8"
    )
    with pytest.raises(audit.AuditError):
        audit.run_audit(root)


# --- audit extensions (w2 s13 scope, spec-first) --------------------------------


def test_audit_route_outcome_lines_per_route(tmp_path):
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2")
    _write_spawn(root, "s1", "a1", "glm", "clean-deliverable")
    _write_spawn(root, "s1", "a2", "glm", "clean-empty")
    # a2 also carries a terminated marker: exit 0 wins the class and the
    # marker is bookkeeping, so the spawn stays clean-empty.
    ws_a2 = root / "rimba" / "s1" / "a2"
    (ws_a2 / "terminated").write_text("terminated\n", encoding="utf-8")
    _write_spawn(root, "s2", "a3", "glm", "failed")
    _write_spawn(root, "s2", "a4", "glm", "not-exited")
    _write_spawn(root, "s2", "a5", "glm", "crashed")
    _write_spawn(root, "s2", "a6", "fable", "clean-deliverable")
    text = audit.run_audit(root).read_text(encoding="utf-8")
    lines = text.splitlines()
    glm = [line for line in lines if "route glm:" in line]
    fable = [line for line in lines if "route fable:" in line]
    assert len(glm) == 1
    assert len(fable) == 1
    want_glm = (
        "route glm: 1 clean-deliverable, 1 clean-empty, 1 failed, "
        "2 not-exited over 5 spawns"
    )
    assert want_glm in glm[0]
    assert "s1" in glm[0] and "s2" in glm[0]  # the line cites its seasons
    want_fable = (
        "route fable: 1 clean-deliverable, 0 clean-empty, 0 failed, "
        "0 not-exited over 1 spawns"
    )
    assert want_fable in fable[0]
    assert "s2" in fable[0] and "s1" not in fable[0]  # only its own evidence
    assert "tool-check" not in text  # one clean-empty is below the trigger


def test_audit_route_two_clean_empty_spawns_tool_check_candidate(tmp_path):
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2")
    _write_spawn(root, "s1", "b1", "sol", "clean-empty")
    _write_spawn(root, "s2", "b2", "sol", "clean-empty")
    text = audit.run_audit(root).read_text(encoding="utf-8")
    want = "route sol: 0 clean-deliverable, 2 clean-empty, 0 failed, 0 not-exited over 2 spawns"
    assert want in text
    hits = [line for line in text.splitlines() if "tool-check" in line]
    assert len(hits) == 1
    assert hits[0].startswith("candidate:")
    assert "clean-empty" in hits[0] and "sol" in hits[0]
    assert "s1" in hits[0] and "s2" in hits[0]


def test_audit_single_masked_loss_is_finding_not_candidate(tmp_path):
    root = _write_audit_proj(tmp_path, sids=("s1", "s2", "s3"))
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2")
    _write_rimba_season(root, "s3")
    _write_harvest_record(root, "s1", "LOSS")
    _write_results_rows(root, "s1", [{"integrated": True, "delta": 0.02}])
    _write_harvest_record(root, "s2", "LOSS")
    _write_results_rows(root, "s2", [{"integrated": False}])  # no value: not masked
    _write_harvest_record(root, "s3", "WIN")
    _write_results_rows(root, "s3", [{"integrated": True}])  # WIN: nothing masked
    text = audit.run_audit(root).read_text(encoding="utf-8")
    hits = [line for line in text.splitlines() if "band masked value" in line]
    assert len(hits) == 1
    assert "s1" in hits[0]
    assert "s2" not in hits[0] and "s3" not in hits[0]
    assert "recalibrate" not in text  # one masked season proposes nothing


def test_audit_two_masked_losses_yield_recalibrate_candidate(tmp_path):
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2")
    _write_harvest_record(root, "s1", "LOSS")
    _write_harvest_record(root, "s2", "LOSS")
    _write_results_rows(root, "s1", [{"integrated": True}])
    _write_results_rows(root, "s2", [{"integrated": False}, {"integrated": True}])
    text = audit.run_audit(root).read_text(encoding="utf-8")
    masked = [line for line in text.splitlines() if "band masked value" in line]
    assert len(masked) == 2
    hits = [line for line in text.splitlines() if "recalibrate LOSS bands" in line]
    assert len(hits) == 1
    assert hits[0].startswith("candidate:")
    assert "s1" in hits[0] and "s2" in hits[0]


def test_audit_missing_cost_cap_is_finding_never_candidate(tmp_path):
    root = _audit_base(tmp_path)  # RUMPUN_YAML carries no campaign block
    text = audit.run_audit(root).read_text(encoding="utf-8")
    hits = [line for line in text.splitlines() if "campaign_cost_cap unset" in line]
    assert len(hits) == 1
    assert not any(
        line.startswith("candidate:") and "campaign_cost_cap" in line
        for line in text.splitlines()
    )


def test_audit_set_cost_cap_clears_budget_finding(tmp_path):
    root = _write_audit_proj(tmp_path, project_yaml=RUMPUN_YAML_CAPPED)
    _write_rimba_season(root, "s1")
    (root / "rimba" / "s2").mkdir(parents=True)
    text = audit.run_audit(root).read_text(encoding="utf-8")
    assert "campaign_cost_cap unset" not in text


def test_audit_candidate_priority_phase_route_calibration(tmp_path):
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2")
    # A third declared phase whose artifact no season wrote arms the
    # dead-phase trigger without touching verdicts.jsonl — the audit's
    # verdict source, which the masked-LOSS rows below need intact.
    latest = root / "musim" / "s2.yaml"
    latest.write_text(
        AUDIT_SEASON.format(sid="s2").replace(
            "    - phase: evaluate\n"
            "      primitive: evaluate\n"
            "      agents: benih\n"
            "      prompt: prompts/dev/dummy.md\n"
            "      writes: verdicts.jsonl\n",
            "    - phase: evaluate\n"
            "      primitive: evaluate\n"
            "      agents: benih\n"
            "      prompt: prompts/dev/dummy.md\n"
            "      writes: verdicts.jsonl\n"
            "    - phase: reflect\n"
            "      primitive: reflect\n"
            "      agents: benih\n"
            "      prompt: prompts/dev/dummy.md\n"
            "      writes: reflections.jsonl\n",
        ),
        encoding="utf-8",
    )
    for sid in ("s1", "s2"):
        _write_harvest_record(root, sid, "LOSS")
        _write_results_rows(root, sid, [{"integrated": True}])
        _write_spawn(root, sid, f"e-{sid}", "sol", "clean-empty")
    text = audit.run_audit(root).read_text(encoding="utf-8")
    candidates = [line for line in text.splitlines() if line.startswith("candidate:")]
    assert len(candidates) == 3  # MAX_CANDIDATES with all three triggers met
    assert "exercise or trim" in candidates[0]
    assert "tool-check" in candidates[1] and "sol" in candidates[1]
    assert "recalibrate LOSS bands" in candidates[2]
    assert "campaign_cost_cap unset" in text  # the finding is present...
    assert not any("campaign_cost_cap" in line for line in candidates)  # ...never proposed


def test_audit_extended_fixture_leaves_musim_rimba_untouched(tmp_path):
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2")
    _write_spawn(root, "s1", "c1", "glm", "clean-deliverable")
    _write_spawn(root, "s1", "c2", "glm", "clean-empty")
    _write_spawn(root, "s2", "c3", "sol", "failed")
    _write_spawn(root, "s2", "c4", "sol", "not-exited")
    _write_harvest_record(root, "s1", "LOSS")
    _write_results_rows(root, "s1", [{"integrated": True}])
    before = {sub: _tree_snapshot(root, sub) for sub in ("musim", "rimba")}
    audit.run_audit(root)
    after = {sub: _tree_snapshot(root, sub) for sub in ("musim", "rimba")}
    assert before == after


def test_audit_route_scan_stops_at_window(tmp_path):
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2")
    _write_spawn(root, "s1", "d1", "glm", "clean-deliverable")
    _write_spawn(root, "s2", "d2", "sol", "clean-empty")
    text = audit.run_audit(root, last_n=1).read_text(encoding="utf-8")
    assert "route glm:" not in text  # the glm spawn sits outside the window
    assert "route sol:" in text


# --- workspaces section (harness: surface rimba/ content in reports) ------------


def test_report_workspace_links(tmp_path):
    root = tmp_path / "proj" / ".rumpun"
    (root / "musim").mkdir(parents=True)
    season = _write_rimba_season(root, "s1")
    state_file = season / "_season" / "state.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["agents"] = {
        "w1": {"name": "w1", "route": "glm", "state": "exited", "exit_code": 0}
    }
    state_file.write_text(json.dumps(state), encoding="utf-8")
    ws = season / "w1"
    ws.mkdir()
    (ws / "agent.log").write_text("stream\n", encoding="utf-8")
    (ws / "prompt.md").write_text("book\n", encoding="utf-8")
    (ws / "results").mkdir()
    (ws / "results" / "notes.md").write_text("analysis\n", encoding="utf-8")
    doc = report.render_report(root, "s1")
    text = doc.read_text(encoding="utf-8")
    assert "<h2>Workspaces [D]</h2>" in text
    assert 'href="w1/agent.log"' in text
    assert 'href="w1/results/notes.md"' in text
    assert 'href="w1/prompt.md"' not in text


def test_discoveries_view_filters_and_renders(tmp_path):
    root = tmp_path / "proj" / ".rumpun"
    (root / "akar").mkdir(parents=True)
    (root / "rimba").mkdir()
    akar.append_record(root, "s1-harvest", "season s1 harvest", "verdict: WIN")
    akar.append_record(root, "approve-s1", "gate approval", "approved")
    akar.append_record(
        root, "glm-toolless-spawn", "tool-less spawns", "7 of 24 boot without tools"
    )
    akar.append_record(root, "audit-1", "reflection audit", "5 dead phases found")
    records = report._discovery_records(root)
    assert [rec["id"] for rec in records] == ["audit-1", "glm-toolless-spawn"]
    out = report.render_discoveries(root)
    text = out.read_text(encoding="utf-8")
    assert "reflection audit" in text and "tool-less spawns" in text
    assert "s1-harvest" not in text and "approve-s1" not in text
    page = (out.parent / "audit-1.html").read_text(encoding="utf-8")
    assert "5 dead phases found" in page
    assert "all discoveries" in page


# --- toolless additive-key safety (harness salvage of s14 w2, stall-terminated) ---


def test_report_document_unchanged_by_toolless_mark():
    """A snap carrying the additive toolless key renders the same bytes."""
    status = {
        "id": "s1",
        "status": "completed",
        "started_at": 1.0,
        "ended_at": 2.0,
        "agents": {
            "w1": {
                "name": "w1",
                "route": "glm",
                "state": "exited",
                "exit_code": 0,
                "seconds": 1.0,
            }
        },
    }
    marked = {
        **status,
        "agents": {"w1": {**status["agents"]["w1"], "toolless": True}},
    }
    base = report._document(status)
    doc = report._document(marked)
    assert doc == base  # the mark must not leak into the rendered report
    assert report._document(marked) == doc  # determinism holds with the mark

def test_audit_f4_route_counts_unchanged_by_toolless_mark(tmp_path):
    """run_audit's F4 outcome counts ignore the additive toolless mark.

    Same fixture, two audit runs, the only delta being toolless: true
    stamped onto both finalized snaps between them: the per-route line
    must come out identical.
    """
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2")
    _write_spawn(root, "s1", "t1", "glm", "clean-deliverable")
    _write_spawn(root, "s2", "t2", "glm", "clean-empty")
    want = (
        "route glm: 1 clean-deliverable, 1 clean-empty, 0 failed, "
        "0 not-exited over 2 spawns"
    )
    before = audit.run_audit(root).read_text(encoding="utf-8")
    assert want in before
    for sid, name in (("s1", "t1"), ("s2", "t2")):
        path = root / "rimba" / sid / "_season" / "state.json"
        state = json.loads(path.read_text(encoding="utf-8"))
        state["agents"][name]["toolless"] = True
        path.write_text(json.dumps(state), encoding="utf-8")
    after = audit.run_audit(root).read_text(encoding="utf-8")
    glm_before = [ln for ln in before.splitlines() if "route glm:" in ln]
    glm_after = [ln for ln in after.splitlines() if "route glm:" in ln]
    assert glm_after == glm_before
    assert want in after


# --- stall semantics (harness hot-fix after s15: runtime killed live spawns) ----


def test_agent_snap_stall_tracks_log_progress_not_runtime(tmp_path):
    """A spawn streaming into agent.log is running however long it runs.

    s15 regression: stalled was computed from started_at alone, so any
    spawn alive past stall_minutes was killed mid-work. Durable progress
    is agent.log growth (mtime); a frozen log past the window stalls.
    """
    ws = tmp_path / "w1"
    ws.mkdir()
    meta = {
        "name": "w1",
        "route": "glm",
        "pid": os.getpid(),
        "proc_start": engine._proc_start_ticks(os.getpid()),
        "started_at": time.time() - 60.0,
    }
    (ws / "state.json").write_text(json.dumps(meta), encoding="utf-8")
    log = ws / "agent.log"
    log.write_text("x\n", encoding="utf-8")
    assert engine._agent_snap(ws, 1.0)["state"] == "running"
    old = time.time() - 30.0
    os.utime(log, (old, old))
    assert engine._agent_snap(ws, 1.0)["state"] == "stalled"


# --- stream tool evidence (w2 s16 scope, spec-first) --------------------------
#
# Spec-first (musim/s16.yaml): these pins run red against the current engine
# (it reads no stream events yet) and green once w1's stream-evidence patch
# lands. Pinned contract:
# - stream_tool_names(text): line-delimited JSON split on newline only (a
#   raw U+2028 inside a JSON string is NOT a line break), tool names from
#   tool_use blocks, empty text -> empty set, malformed lines skipped with
#   one DEBUG log each (blank lines stay silent).
# - file_tools lifecycle: sticky true on the first file-tool event;
#   ToolSearch/WebFetch/Task/Agent never mark; false only at finalize with
#   >= 1 parseable event and zero file-tool events; absent when the stream
#   held zero parseable events (never guessed).
# - stream_offset: additive over appended bytes; a scan over unchanged
#   bytes re-classifies nothing.
# - Truncated real s15 streams replay to file_tools true for both writers.
# - file_tools/stream_offset are additive keys: report bytes and audit F4
#   counts never change.
# - Scanning rides the existing watch cycle (no new polling).
#
# The gate-hardening pins are spec-first (s17, w2; carried by s18, w2):
# benih name containment lands in w2's lint.py copy (H4); finalize locking
# (H1) and akar append serialization (H6) land at integration in w1's
# engine.py / akar.py. Expected red against the current tree is measured
# and recorded in this season's w2 workspace notes.


def _stream_event(tool: str) -> str:
    """One synthetic assistant stream-json event carrying a tool_use block."""
    block = {
        "type": "tool_use",
        "id": f"call_{tool}",
        "name": tool,
        "input": {"path": "n.md"},
    }
    event = {"type": "assistant", "message": {"role": "assistant", "content": [block]}}
    return json.dumps(event, ensure_ascii=False)


def _stream_text(*tools: str) -> str:
    """Line-delimited stream events, one per tool, each closed by a newline."""
    return "".join(_stream_event(t) + "\n" for t in tools)


def _stream_ws(tmp_path):
    """Agent workspace under a .rumpun-shaped root; returns (root, ws).

    state.json mirrors an engine spawn whose pid 1 / proc_start pair never
    matches a live process, so scans and finalize see a dead spawn.
    """
    root = tmp_path / "proj" / ".rumpun"
    ws = root / "rimba" / "s1" / "w1"
    ws.mkdir(parents=True)
    (ws / "state.json").write_text(
        json.dumps(
            {
                "name": "w1",
                "route": "glm",
                "cmd": "x",
                "pid": 1,
                "proc_start": 987654321,
                "started_at": 0.0,
            }
        ),
        encoding="utf-8",
    )
    return root, ws


def _stream_scan(root, ws):
    """Run the engine's stream scan under whichever internal signature lands.

    The two s16 documents disagree on the private shape: the w1 prompt
    writes _scan_agent_stream(ws, meta); the s15 salvage block writes
    _scan_agent_stream(root, sid, ws). The pinned contract is behavior
    (state.json gains stream_offset / file_tools), not the signature, so
    either shape runs here.
    """
    params = list(inspect.signature(engine._scan_agent_stream).parameters)
    if params == ["root", "sid", "ws"]:
        engine._scan_agent_stream(root, "s1", ws)
    else:
        meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
        engine._scan_agent_stream(ws, meta)


def _finalize_fixture(tmp_path, log_text):
    """rimba/s1 holding w1's workspace plus a running _season/state.json.

    spawned lists w1 with a pid/proc_start pair that is never alive, so
    _finalize classifies the stream without terminating anything.
    """
    root, ws = _stream_ws(tmp_path)
    if log_text is not None:
        (ws / "agent.log").write_text(log_text, encoding="utf-8")
    season = root / "rimba" / "s1" / "_season"
    season.mkdir()
    (season / "state.json").write_text(
        json.dumps(
            {
                "id": "s1",
                "status": "running",
                "started_at": 1.0,
                "spawned": {"w1": {"pid": 1, "proc_start": 987654321}},
            }
        ),
        encoding="utf-8",
    )
    return root, ws


def test_stream_tool_names_empty_text_yields_no_tools():
    assert engine.stream_tool_names("") == set()


def test_stream_tool_names_collects_names_and_ignores_other_blocks():
    event = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "running the check"},
                {"type": "tool_use", "id": "c1", "name": "Bash", "input": {}},
                {"type": "tool_use", "id": "c2", "name": "WebFetch", "input": {}},
            ],
        },
    }
    assert engine.stream_tool_names(json.dumps(event) + "\n") == {"Bash", "WebFetch"}


def test_stream_tool_names_skips_malformed_lines_with_one_debug_each(caplog):
    text = (
        _stream_event("Bash")
        + "\n"
        + "this line is not json\n"
        + "\n"
        + _stream_event("WebFetch")
        + "\n"
    )
    with caplog.at_level(logging.DEBUG, logger="rumpun.engine"):
        names = engine.stream_tool_names(text)
    assert names == {"Bash", "WebFetch"}
    debug = [
        r
        for r in caplog.records
        if r.name == "rumpun.engine" and r.levelno == logging.DEBUG
    ]
    assert len(debug) == 1  # one per malformed line; the blank line stays silent


def test_stream_tool_names_u2028_inside_json_is_not_a_line_break():
    raw = chr(0x2028)  # LINE SEPARATOR: splitlines() breaks here; split("\n") must not
    line = _stream_event("Bash").replace("n.md", f"a{raw}b")
    assert raw in line  # the raw separator rode inside the JSON string value
    assert "\n" not in line  # one physical line: newline splitting keeps it whole
    assert engine.stream_tool_names(line + "\n") == {"Bash"}


def test_scan_agent_stream_marks_file_tools_on_first_file_tool_event(tmp_path):
    root, ws = _stream_ws(tmp_path)
    text = _stream_text("ToolSearch", "Bash")
    (ws / "agent.log").write_text(text, encoding="utf-8")
    _stream_scan(root, ws)
    meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    assert meta["file_tools"] is True
    assert meta["stream_offset"] == len(text)  # advanced additively to log end


def test_scan_agent_stream_toolsearch_class_never_marks(tmp_path):
    root, ws = _stream_ws(tmp_path)
    text = _stream_text("ToolSearch", "WebFetch", "Task", "Agent")
    (ws / "agent.log").write_text(text, encoding="utf-8")
    _stream_scan(root, ws)
    meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    assert "file_tools" not in meta  # mid-stream: only finalize may set false
    assert meta["stream_offset"] == len(text)  # bytes consumed even without a mark


def test_finalize_sets_file_tools_false_after_parseable_non_file_stream(tmp_path):
    root, _ws = _finalize_fixture(tmp_path, _stream_text("ToolSearch"))
    state = engine._finalize(root, "s1", "completed", {})
    assert state["agents"]["w1"]["file_tools"] is False
    persisted = engine._load_state(root, "s1")
    assert persisted["agents"]["w1"]["file_tools"] is False


def test_finalize_leaves_file_tools_absent_when_zero_parseable_events(tmp_path):
    root, _ws = _finalize_fixture(tmp_path, "")
    state = engine._finalize(root, "s1", "completed", {})
    assert "file_tools" not in state["agents"]["w1"]
    assert "file_tools" not in engine._load_state(root, "s1")["agents"]["w1"]


def test_finalize_marks_file_tools_true_when_stream_had_a_file_tool_event(tmp_path):
    root, _ws = _finalize_fixture(tmp_path, _stream_text("ToolSearch", "Read"))
    state = engine._finalize(root, "s1", "completed", {})
    assert state["agents"]["w1"]["file_tools"] is True
    assert engine._load_state(root, "s1")["agents"]["w1"]["file_tools"] is True


def test_scan_agent_stream_offset_additive_and_no_reclassification(tmp_path, monkeypatch):
    root, ws = _stream_ws(tmp_path)
    first = _stream_text("Bash")
    (ws / "agent.log").write_text(first, encoding="utf-8")
    _stream_scan(root, ws)
    meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    assert meta["stream_offset"] == len(first)

    calls: list[str] = []
    real = engine._parse_stream_events

    def spy(text):
        calls.append(text)
        return real(text)

    monkeypatch.setattr(engine, "_parse_stream_events", spy)
    second = _stream_text("ToolSearch")
    with (ws / "agent.log").open("a", encoding="utf-8") as fh:
        fh.write(second)
    _stream_scan(root, ws)
    meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    assert meta["stream_offset"] == len(first) + len(second)  # additive
    assert meta["file_tools"] is True  # sticky: ToolSearch alone never unsets
    assert len(calls) == 1  # only the appended bytes went through the parser

    _stream_scan(root, ws)  # unchanged bytes: re-classifies nothing
    meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    assert meta["stream_offset"] == len(first) + len(second)
    assert len(calls) == 1


def _repo_root():
    """Nearest ancestor holding the .rumpun tree.

    At the merged location (repo tests/) this is the repo root; the same
    resolution works when this file runs from a season workspace copy.
    """
    return next(
        (p for p in Path(__file__).resolve().parents if (p / ".rumpun").is_dir()),
        None,
    )


S15_STREAM_BYTES = 200 * 1024  # 200 KiB, not 200_000: measured, w1's first
# tool_use sits at byte 202605 and w2's at 196577, so a 200_000-byte cut
# would hold no file-tool event for w1 at all and the s16 band ("both
# writers true") would be unreachable.


@pytest.mark.parametrize("writer", ["w1", "w2"])
def test_real_stream_replay_marks_writer_file_tools(tmp_path, writer):
    base = _repo_root()
    src = (
        None
        if base is None
        else base / ".rumpun" / "rimba" / "s15" / writer / "agent.log"
    )
    if src is None or not src.is_file():
        pytest.skip(f"real-stream fixture not in this clone: {src}")
    root, ws = _stream_ws(tmp_path)
    shutil.copyfile(src, ws / "agent.log")
    with (ws / "agent.log").open("r+b") as fh:
        fh.truncate(S15_STREAM_BYTES)
    _stream_scan(root, ws)
    meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    assert meta["file_tools"] is True


def test_report_document_unchanged_by_file_tools_marks():
    """Additive stream keys never leak into the rendered report (s14 pattern)."""
    status = {
        "id": "s1",
        "status": "completed",
        "started_at": 1.0,
        "ended_at": 2.0,
        "spawned": {"w1": {"pid": 7, "proc_start": 99}},
        "agents": {
            "w1": {
                "name": "w1",
                "route": "glm",
                "state": "exited",
                "exit_code": 0,
                "seconds": 1.0,
            }
        },
    }
    marked = {
        **status,
        "spawned": {"w1": {"pid": 7, "proc_start": 99, "stream_offset": 12345}},
        "agents": {
            "w1": {
                **status["agents"]["w1"],
                "file_tools": True,
                "stream_offset": 12345,
            }
        },
    }
    base = report._document(status)
    marked_doc = report._document(marked)
    assert marked_doc == base  # the marks must not leak into the report
    assert report._document(marked) == marked_doc  # determinism holds


def test_audit_f4_route_counts_unchanged_by_file_tools_marks(tmp_path):
    """run_audit's F4 outcome counts ignore the additive stream keys.

    Same fixture, two audit runs, the only delta being file_tools and
    stream_offset stamped onto both finalized snaps between them: the
    per-route line must come out identical.
    """
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2")
    _write_spawn(root, "s1", "t1", "glm", "clean-deliverable")
    _write_spawn(root, "s2", "t2", "glm", "clean-empty")
    want = (
        "route glm: 1 clean-deliverable, 1 clean-empty, 0 failed, "
        "0 not-exited over 2 spawns"
    )
    before = audit.run_audit(root).read_text(encoding="utf-8")
    assert want in before
    for sid, name in (("s1", "t1"), ("s2", "t2")):
        path = root / "rimba" / sid / "_season" / "state.json"
        state = json.loads(path.read_text(encoding="utf-8"))
        state["agents"][name]["file_tools"] = True
        state["agents"][name]["stream_offset"] = 204800
        path.write_text(json.dumps(state), encoding="utf-8")
    after = audit.run_audit(root).read_text(encoding="utf-8")
    glm_before = [ln for ln in before.splitlines() if "route glm:" in ln]
    glm_after = [ln for ln in after.splitlines() if "route glm:" in ln]
    assert glm_after == glm_before
    assert want in after


RUMPUN_YAML_STREAM = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "cat {prompt}; sleep 3"
"""


def test_watch_cycle_scans_stream_and_finalizes_marks(tmp_path, monkeypatch):
    """Scanning rides the existing watch cycle; finalize classifies the rest.

    The route cats a stream-json fixture into agent.log, stays alive past
    the first watch cycles, then exits 0. start_season must reach completed
    with agents.w1.file_tools true, and the scan must have been invoked from
    the existing loop -- no new polling mechanism.
    """
    root, season = _write_proj(tmp_path, SEASON_S1, project_yaml=RUMPUN_YAML_STREAM)
    (root / "prompts" / "dev" / "dummy.md").write_text(
        _stream_text("ToolSearch", "Bash"), encoding="utf-8"
    )
    scan_calls: list[int] = []
    real_scan = engine._scan_agent_stream

    def counting_scan(*args, **kwargs):
        scan_calls.append(1)
        return real_scan(*args, **kwargs)

    monkeypatch.setattr(engine, "_scan_agent_stream", counting_scan)
    state = engine.start_season(season, root)
    assert state["status"] == "completed"
    assert state["agents"]["w1"]["file_tools"] is True
    ws_meta = json.loads(
        (root / "rimba" / "s1" / "w1" / "state.json").read_text(encoding="utf-8")
    )
    assert ws_meta["stream_offset"] > 0
    assert len(scan_calls) >= 1  # the scan rode the watch cycle, not a new poller


# --- s17 w2: gate hardening (spec-first) ---------------------------------------
#
# Pinned contracts: H4 (benih name containment) lands in w2's lint.py copy;
# H1 (finalize locking) and H6 (akar append serialization) land at
# integration in w1's engine.py/akar.py. Red against the current tree is
# expected; the measured set lives in this season's w2 workspace notes.

# H1 fixture: each stub route touches its marker as its first command, then
# sleeps far past any realistic test duration. Markers prove
# ran-versus-never-ran; termination is proven by process death against the
# recorded pid/proc_start, never by wall-clock timing.
RUMPUN_YAML_STOP_TEMPLATE = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm_w1: "cat {{prompt}} > /dev/null; touch {w1_marker}; sleep 120"
  glm_w2: "cat {{prompt}} > /dev/null; touch {w2_marker}; sleep 120"
"""

SEASON_STOP = """\
id: s1
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
    eval_window: "s1"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
benih:
  - name: w1
    route: glm_w1
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 1}
  - name: w2
    route: glm_w2
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 1}
stop:
  "on": [all_exited, {stall_minutes: 15}]
"""


@pytest.mark.parametrize(
    ("bad_name", "fragment"),
    [
        ("../../x", "../../x"),
        ("_season", "_season"),
        ("a/b", "a/b"),
        ("", "non-empty"),
        (".hidden", ".hidden"),
        ("a" * 33, "a" * 33),
    ],
)
def test_lint_rejects_uncontained_benih_name(tmp_path, bad_name, fragment):
    """H4 pin: off-containment names are lint errors naming the benih."""
    season_text = SEASON_S1.replace("name: w1", f'name: "{bad_name}"')
    _root, season = _write_proj(tmp_path, season_text)
    findings = lint.lint(season)
    hits = [f for f in findings if f.severity == "error" and fragment in f.message]
    assert hits, f"lint accepted benih name {bad_name!r}: {[f.message for f in findings]}"


@pytest.mark.parametrize("good_name", ["w1", "alpha-1", "w2_x"])
def test_lint_accepts_contained_benih_name(tmp_path, good_name):
    """H4 pin: contained names add no errors (s1-s17 names stay valid)."""
    season_text = SEASON_S1.replace("name: w1", f"name: {good_name}")
    _root, season = _write_proj(tmp_path, season_text)
    findings = lint.lint(season)
    assert [f for f in findings if f.severity == "error"] == []


def test_akar_append_same_id_under_barrier_admits_one_writer(tmp_path):
    """H6 pin: two barrier-synchronized same-id appends admit one writer.

    Exactly one append_record succeeds; the other raises AkarError; the
    published body matches the winner; akar/ holds exactly one file for the
    id. Red today: the duplicate check and the publish do not serialize, so
    both threads pass the check and the second replace silently wins.
    """
    import threading

    bodies = {0: "body from writer zero", 1: "body from writer one"}
    barrier = threading.Barrier(2)
    outcomes: dict[int, str] = {}

    def attempt(k: int) -> None:
        barrier.wait()
        try:
            akar.append_record(tmp_path, "race-1", "concurrent append", bodies[k])
            outcomes[k] = "ok"
        except akar.AkarError:
            outcomes[k] = "error"

    threads = [threading.Thread(target=attempt, args=(k,)) for k in (0, 1)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)
    assert set(outcomes) == {0, 1}  # neither thread died mid-append
    winners = [k for k, v in outcomes.items() if v == "ok"]
    losers = [k for k, v in outcomes.items() if v == "error"]
    assert len(winners) == 1, f"expected exactly one winner, got {outcomes}"
    assert losers == [1 - winners[0]]
    records = list((tmp_path / "akar").glob("*_race-1.md"))
    assert len(records) == 1
    text = records[0].read_text(encoding="utf-8")
    assert bodies[winners[0]] in text
    assert bodies[1 - winners[0]] not in text


def test_stop_racing_spawn_tracks_and_kills_every_spawn(tmp_path, monkeypatch):
    """H1 pin: a stop racing the spawn loop leaves zero live untracked agents.

    The second benih's admission is held inside the starter's spawn cycle
    until the stop's final state write is underway. Today's engine finalizes
    from a stale snapshot, so the held spawn lands untracked while its stub
    keeps running. The pin checks the invariant: every admitted spawn is in
    the final spawned and agents maps and its process is dead; a
    never-admitted name has no workspace state and no marker. The stub's
    first command touches a marker proving ran-versus-never-ran; no
    wall-clock assertions.
    """
    import signal
    import threading
    from contextlib import suppress

    sdir = tmp_path / "proj" / ".rumpun" / "rimba" / "s1"
    project = RUMPUN_YAML_STOP_TEMPLATE.format(
        w1_marker=str(sdir / "w1" / "started.marker"),
        w2_marker=str(sdir / "w2" / "started.marker"),
    )
    root, season = _write_proj(tmp_path, SEASON_STOP, project_yaml=project)

    w1_saved = threading.Event()
    stop_published = threading.Event()
    real_child_env = engine._child_env
    real_save_state = engine._save_state
    env_calls: list[int] = []

    def gated_child_env(r, s, group):
        second = bool(env_calls)
        env_calls.append(1)
        env = real_child_env(r, s, group)
        if second:
            # w1's full spawn cycle (its save included) is done. Hold w2
            # inside the spawn cycle until the stop is publishing its final
            # state: today that makes the stop finalize from a stale
            # snapshot; with H1 fixed the stop simply serializes behind the
            # cycle and the gate's 8s escape expires unused.
            w1_saved.set()
            stop_published.wait(8)
        return env

    def saving_state(*args, **kwargs):
        if threading.current_thread() is threading.main_thread():
            stop_published.set()  # the stop thread is writing its final state
        return real_save_state(*args, **kwargs)

    monkeypatch.setattr(engine, "_child_env", gated_child_env)
    monkeypatch.setattr(engine, "_save_state", saving_state)

    def run_season():
        engine.start_season(season, root)

    starter = threading.Thread(target=run_season, daemon=True)
    starter.start()
    assert w1_saved.wait(15)  # w1 spawned and saved; w2 is held at the gate
    running = engine._load_state(root, "s1")
    assert running is not None and running["status"] == "running"
    try:
        engine.stop_season(root, "s1")
        starter.join(30)
        assert not starter.is_alive()  # the watcher settled behind the stop
        final = engine._load_state(root, "s1")
        assert final is not None
        assert final["status"] != "running"  # terminal, and it stays terminal
        for name in ("w1", "w2"):
            ws = sdir / name
            meta_path = ws / "state.json"
            if not meta_path.is_file():
                # never admitted: nothing may claim it, the stub never ran
                assert not (ws / "started.marker").is_file()
                assert name not in final.get("spawned", {})
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            assert (ws / "started.marker").is_file(), f"{name} ran, no marker"
            assert name in final["spawned"], f"{name} admitted but untracked"
            assert name in final.get("agents", {}), f"{name} not in final agents"
            assert not engine._alive(meta["pid"], meta["proc_start"]), (
                f"{name} outlived the stop"
            )
    finally:
        for name in ("w1", "w2"):
            meta_path = sdir / name / "state.json"
            if not meta_path.is_file():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if engine._alive(meta["pid"], meta["proc_start"]):
                with suppress(OSError):
                    os.killpg(meta["pid"], signal.SIGKILL)


# --- s18 w2: warning-transition pin ---------------------------------------------
#
# The s16 stream detector emits its WARNING from _mark_file_tools, which
# _scan_agent_stream calls on every chunk holding a file-tool sighting.
# The ratified contract (docstring: "Called only on the true transition;
# true is sticky, so this never repeats") is one WARNING per agent stream.
# The fix lands at integration in w1's engine.py; red against the current
# tree is expected and measured in this season's w2 workspace notes.


def test_stream_warning_emits_once_across_sightings(tmp_path, caplog):
    """Warning-transition pin: N sightings over M scans -> exactly one WARNING.

    A synthetic stream holds file-tool sightings in two separately scanned
    chunks. The second scan consumes new bytes (stream_offset advances past
    the first chunk) yet must not emit a second rumpun.engine WARNING: the
    mark rides the sticky true transition, never per-sighting. No wall
    clock: each scan is called directly.
    """
    root = tmp_path / "proj" / ".rumpun"
    ws = root / "rimba" / "s1" / "w1"
    ws.mkdir(parents=True)
    meta: dict = {"name": "w1", "stream_offset": 0}
    log_path = ws / "agent.log"

    log_path.write_text(_stream_text("Bash", "Bash"), encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="rumpun.engine"):
        engine._scan_agent_stream(ws, meta)
        first_offset = meta["stream_offset"]
        log_path.write_text(
            log_path.read_text(encoding="utf-8") + _stream_text("Read"), encoding="utf-8"
        )
        engine._scan_agent_stream(ws, meta)  # second chunk, another sighting

    assert meta["file_tools"] is True
    assert meta["stream_offset"] > first_offset > 0  # chunk two was consumed
    warnings = [
        record
        for record in caplog.records
        if record.name == "rumpun.engine" and record.levelno >= logging.WARNING
    ]
    assert len(warnings) == 1, (
        f"expected one WARNING for the true transition, got {len(warnings)}: "
        f"{[r.getMessage() for r in warnings]}"
    )


# --- state hook (harness: landing page truthful mid-season) ---------------------


RUMPUN_YAML_SLOW = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "sleep 3; cat {prompt} > /dev/null"
"""


def test_watch_cycle_refreshes_index_hook(tmp_path):
    """state_hook fires once per watcher cycle while the season runs."""
    root, season = _write_proj(tmp_path, SEASON_S1, project_yaml=RUMPUN_YAML_SLOW)
    calls: list[int] = []
    engine.state_hook = lambda: calls.append(1)
    try:
        state = engine.start_season(season, root)
    finally:
        engine.state_hook = None
    assert state["status"] == "completed"
    assert len(calls) >= 2  # a 3s stub crosses at least two 1s cycles
    assert engine.state_hook is None  # the verb clears it in finally


def test_state_hook_failure_never_kills_watcher(tmp_path):
    """A raising hook is logged and ignored; the season still completes."""
    root, season = _write_proj(tmp_path, SEASON_S1, project_yaml=RUMPUN_YAML_SLOW)

    def bad():
        raise RuntimeError("hook boom")

    engine.state_hook = bad
    try:
        state = engine.start_season(season, root)
    finally:
        engine.state_hook = None
    assert state["status"] == "completed"


# --- s31 w2: render-on-change pins (spec-first) ----------------------------------
#
# state_hook currently fires unconditionally once per watcher cycle (the watch
# loop in engine.py); the s30 launch produced ~1600 identical index renders for
# one season because no engine write touches the persisted state.json between
# spawn and finalize. The ratified s31 contract: hash the persisted state.json
# bytes before the hook call; render on the first cycle of a fresh watcher,
# then only when the bytes change. The gate pins hook-invocation counts, never
# wall-clock timing. Pins red against the current tree are expected; the
# measured set lives in this workspace's notes.md.


def test_hook_change_gate_quiet_season_renders_once(tmp_path):
    """Quiet-season pin: state bytes never change -> exactly one render.

    A 3s quiet stub crosses ~4 watcher cycles. No engine write happens
    between spawn and finalize, so the persisted state.json bytes never
    change; the change gate must pass the hook exactly once.
    """
    root, season = _write_proj(tmp_path, SEASON_S1, project_yaml=RUMPUN_YAML_SLOW)
    calls: list[int] = []
    engine.state_hook = lambda: calls.append(1)
    try:
        state = engine.start_season(season, root)
    finally:
        engine.state_hook = None
    assert state["status"] == "completed"
    assert len(calls) == 1, (
        f"quiet season rendered {len(calls)}x; the gate allows exactly one"
        " render while the persisted state bytes never change"
    )


def test_hook_change_gate_byte_change_rerenders_once(tmp_path):
    """Byte-change pin: one mid-run byte change -> exactly one re-render.

    The counting hook signals a helper thread after the first render; the
    thread rewrites the persisted state.json between cycles (same shape,
    new bytes: same dict re-dumped with sorted keys). No engine write
    happens mid-run, so the unlocked rewrite cannot race finalize. The
    gate must fire the hook exactly once more, whatever inter-cycle
    boundary the rewrite lands on.
    """
    root, season = _write_proj(tmp_path, SEASON_S1, project_yaml=RUMPUN_YAML_SLOW)
    calls: list[int] = []
    first_render = threading.Event()
    rewrote = threading.Event()

    def hook() -> None:
        calls.append(1)
        if len(calls) == 1:
            first_render.set()

    def rewrite_state_once() -> None:
        if not first_render.wait(timeout=5):
            return
        time.sleep(0.5)  # land on an inter-cycle boundary, not inside cycle 1
        path = engine.state_path(root, "s1")
        state = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8",
        )
        rewrote.set()

    rewriter = threading.Thread(target=rewrite_state_once, daemon=True)
    rewriter.start()
    engine.state_hook = hook
    try:
        state = engine.start_season(season, root)
    finally:
        engine.state_hook = None
        rewriter.join(timeout=2)
    assert state["status"] == "completed"
    assert rewrote.is_set(), "helper rewrite never ran; pin measured nothing"
    assert len(calls) == 2, (
        f"one byte change must re-render exactly once (total 2), got {len(calls)}"
    )


def test_hook_first_cycle_renders_before_any_change(tmp_path):
    """First-cycle pin: a fresh watcher renders before any byte change.

    The hook records whether the stub has exited at each invocation. The
    first render must precede the stub's exit (cycle 1), so a naive gate
    that only renders on change and skips the never-rendered first cycle
    fails this pin with an empty call log.
    """
    root, season = _write_proj(tmp_path, SEASON_S1, project_yaml=RUMPUN_YAML_SLOW)
    exited: list[bool] = []

    def hook() -> None:
        exit_file = root / "rimba" / "s1" / "w1" / "exit"
        exited.append(exit_file.is_file())

    engine.state_hook = hook
    try:
        state = engine.start_season(season, root)
    finally:
        engine.state_hook = None
    assert state["status"] == "completed"
    assert exited, "no render ever fired; the first cycle must always render"
    assert exited[0] is False, (
        "first render fired after the stub exited; a fresh watcher renders"
        " on its first cycle, before any change"
    )


# --- s19 w2: citation digest enforcement + H2/H3 pins (spec-first) ---------------
#
# H7 lands in w2's lint.py copy (this workspace's lint.py, merged by the
# harness). H2/H3 land at integration in w1's engine.py; red against the
# current tree is expected. The measured set lives in this workspace's
# notes.md.

# H7 fixture: one real akar record (append_record) and the digest akar
# recorded for its body; citations carry that digest (full or prefix).
H7_BODY = "h7 repro body: the evolution gate must reject altered evidence\n"
H7_DIGEST = hashlib.sha256(H7_BODY.encode("utf-8")).hexdigest()


def _h7_proj(tmp_path, citation):
    """Scratch project whose s1 season cites exactly one akar record."""
    season_text = SEASON_S1.replace("evidence: []", f'evidence: ["{citation}"]')
    return _write_proj(tmp_path, season_text)  # (root, season_path)


def test_lint_citation_matching_digest_resolves(tmp_path):
    """H7 pin: the full recorded digest resolves with no lint errors."""
    root, season = _h7_proj(tmp_path, f"akar:h7-doc@{H7_DIGEST}")
    akar.append_record(root, "h7-doc", "h7 fixture", H7_BODY)
    findings = lint.lint(season)
    assert [f for f in findings if f.severity == "error"] == []


def test_lint_citation_tampered_digest_is_error(tmp_path):
    """H7 pin: a wrong digest is an error naming the citation verbatim."""
    citation = f"akar:h7-doc@{'0' * 64}"
    root, season = _h7_proj(tmp_path, citation)
    akar.append_record(root, "h7-doc", "h7 fixture", H7_BODY)
    findings = lint.lint(season)
    hits = [f for f in findings if f.severity == "error" and citation in f.message]
    assert hits, f"lint accepted a tampered digest: {[f.message for f in findings]}"


def test_lint_citation_tampered_record_body_is_error(tmp_path):
    """H7 pin: an altered record body fails against the ORIGINAL citation."""
    citation = f"akar:h7-doc@{H7_DIGEST}"
    root, season = _h7_proj(tmp_path, citation)
    akar.append_record(root, "h7-doc", "h7 fixture", H7_BODY)
    record = akar.find_record(root, "h7-doc")
    text = record.read_text(encoding="utf-8")
    record.write_text(
        text.replace(H7_BODY, "tampered: the gate must catch this\n"), encoding="utf-8"
    )
    findings = lint.lint(season)
    hits = [f for f in findings if f.severity == "error" and citation in f.message]
    assert hits, f"lint accepted altered evidence: {[f.message for f in findings]}"


def test_lint_citation_8char_prefix_resolves(tmp_path):
    """H7 pin: a unique prefix of 8 hex chars resolves (regex floor)."""
    root, season = _h7_proj(tmp_path, f"akar:h7-doc@{H7_DIGEST[:8]}")
    akar.append_record(root, "h7-doc", "h7 fixture", H7_BODY)
    findings = lint.lint(season)
    assert [f for f in findings if f.severity == "error"] == []


def test_lint_citation_too_short_digest_is_error(tmp_path):
    """H7 pin: under 8 hex chars the citation syntax itself fails."""
    citation = f"akar:h7-doc@{H7_DIGEST[:7]}"
    root, season = _h7_proj(tmp_path, citation)
    akar.append_record(root, "h7-doc", "h7 fixture", H7_BODY)
    findings = lint.lint(season)
    hits = [f for f in findings if f.severity == "error" and citation in f.message]
    assert hits, f"lint accepted a 7-char digest: {[f.message for f in findings]}"


def test_lint_citation_partial_id_is_error(tmp_path):
    """H7 pin: a partial record id does not resolve (reviewer's repro)."""
    citation = "akar:h7-do@00000000"  # "h7-do" is a substring of id h7-doc
    root, season = _h7_proj(tmp_path, citation)
    akar.append_record(root, "h7-doc", "h7 fixture", H7_BODY)
    findings = lint.lint(season)
    hits = [f for f in findings if f.severity == "error" and citation in f.message]
    assert hits, f"lint accepted a partial id: {[f.message for f in findings]}"


def _h2_stub(marker):
    """Stub agent in its own session: the SIGTERM trap touches the marker.

    sleep 60 shares the process group, so killpg SIGTERM ends it at once and
    the shell runs the trap immediately: no wall-clock waits in either pin.
    """
    return subprocess.Popen(
        ["/bin/sh", "-c", f'trap "touch {marker}; exit 0" TERM; sleep 60'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def test_terminate_matching_proc_start_signals(tmp_path):
    """H2 pin: with recorded proc_start == live proc_start, the pid is signaled.

    Call shape for w1's patch: engine._terminate(ws, pid, proc_start).
    """
    import signal
    from contextlib import suppress

    ws = tmp_path / "ws"
    ws.mkdir()
    marker = tmp_path / "sig.marker"
    proc = _h2_stub(marker)
    try:
        start = engine._proc_start_ticks(proc.pid)
        assert start is not None
        engine._terminate(ws, proc.pid, start)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("matching proc_start never signaled: process survived")
        assert not engine._alive(proc.pid, start)
    finally:
        with suppress(OSError):
            os.killpg(proc.pid, signal.SIGKILL)


def test_terminate_mismatched_proc_start_warns_and_spares(tmp_path, caplog):
    """H2 pin: a recycled/unknown pid is NOT signaled; one WARNING is logged."""
    import signal
    from contextlib import suppress

    ws = tmp_path / "ws"
    ws.mkdir()
    marker = tmp_path / "sig.marker"
    proc = _h2_stub(marker)
    try:
        start = engine._proc_start_ticks(proc.pid)
        assert start is not None
        with caplog.at_level(logging.WARNING, logger="rumpun.engine"):
            engine._terminate(ws, proc.pid, start + 1)
        assert proc.poll() is None, "stub was signaled despite mismatched proc_start"
        assert not marker.is_file()
        warnings = [
            r
            for r in caplog.records
            if r.name == "rumpun.engine" and r.levelno >= logging.WARNING
        ]
        assert warnings, "no rumpun.engine WARNING for the spared pid"
    finally:
        with suppress(OSError):
            os.killpg(proc.pid, signal.SIGKILL)


def test_terminate_none_proc_start_never_signals(tmp_path, caplog):
    """H2 pin: no recorded identity -> no signal (never kills an unknown pid)."""
    import signal
    from contextlib import suppress

    ws = tmp_path / "ws"
    ws.mkdir()
    marker = tmp_path / "sig.marker"
    proc = _h2_stub(marker)
    try:
        with caplog.at_level(logging.WARNING, logger="rumpun.engine"):
            engine._terminate(ws, proc.pid, None)
        assert proc.poll() is None, "stub was signaled with no recorded proc_start"
        assert not marker.is_file()
        warnings = [
            r
            for r in caplog.records
            if r.name == "rumpun.engine" and r.levelno >= logging.WARNING
        ]
        assert warnings
    finally:
        with suppress(OSError):
            os.killpg(proc.pid, signal.SIGKILL)


# H3 fixture: the route writes pwd to an absolute path, so the file location
# never depends on the caller's working directory (current engine sets no
# cwd and the reviewer's pwd route printed the repository directory).
RUMPUN_YAML_PWD = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "pwd > {cwd_out}"
"""


def test_engine_spawns_agent_inside_workspace_cwd(tmp_path):
    """H3 pin: the spawned agent's cwd is its workspace (reviewer's pwd repro)."""
    ws = tmp_path / "proj" / ".rumpun" / "rimba" / "s1" / "w1"
    project = RUMPUN_YAML_PWD.format(cwd_out=str(ws / "cwd.txt"))
    root, season = _write_proj(tmp_path, SEASON_S1, project_yaml=project)
    state = engine.start_season(season, root)
    assert state["status"] == "completed"
    reported = (ws / "cwd.txt").read_text(encoding="utf-8").strip()
    assert Path(reported).resolve() == ws.resolve()


# --- s20 w2: rejected/rejected-rollback lifecycle + H5/H9 pins (spec-first) ------
#
# H8's apply and rollback legs land in this workspace's evolve.py copy (the
# harness merges it); the start-refusal leg, H5, and H9 land at integration
# in w1's engine.py. Red against the current tree is expected; the measured
# set lives in this workspace's notes.md. Pinned contracts:
# - evolve.apply refuses a season whose id carries a reject-<sid> akar
#   record (exact declared-id resolution, the way citations resolve); a
#   clean season still applies, and another sid's reject record never
#   blocks.
# - evolve.rollback_season on an ACTIVE season (state status running) stops
#   it first via engine.stop_season in the caller's thread, then records
#   containment: the call order is exactly ["stop", "record"].
# - season start refuses a season yaml outside musim/ canonical placement:
#   a rejected file at musim/rejected/<sid>.yaml raises EngineError and
#   creates no season state.
# - H5: a mid-spawn route failure raises EngineError AND leaves no live
#   untracked child: every stub that ran is registered (workspace
#   state.json) and dead.
# - H9: per-agent budgets are per-agent deadlines -- the short-budget benih
#   is terminated at its own deadline while the long-budget sibling
#   completes normally. The season deadline is not max(agent budgets).

# H5/rollback/H9 fixture: marker stubs (the s17 pattern). Markers prove
# ran-versus-never-ran; termination is proven by process death against the
# recorded pid/proc_start, never by wall-clock timing.
RUMPUN_YAML_H5 = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm_w1: "cat {{prompt}} > /dev/null; touch {w1_marker}; sleep 120"
"""

SEASON_BUDGET = """\
id: s1
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
    eval_window: "s1"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
benih:
  - name: short
    route: glm_short
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 0.05}
  - name: long
    route: glm_long
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 10}
stop:
  "on": [all_exited, {stall_minutes: 20}]
"""

RUMPUN_YAML_BUDGET = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm_short: "cat {{prompt}} > /dev/null; touch {short_marker}; sleep 120"
  glm_long: "cat {{prompt}} > /dev/null; sleep 8; touch {long_marker}"
"""


def test_apply_refuses_rejected_season(tmp_path):
    """H8 pin: apply refuses a season id that carries a reject-<sid> record."""
    root, season = _write_proj(tmp_path, SEASON_S1)
    akar.append_record(root, "reject-s1", "season s1 rejected", "fixture rejection")
    with pytest.raises(evolve.EvolveError, match="rejected"):
        evolve.apply(root, season)


def test_apply_passes_clean_season_without_reject_record(tmp_path):
    """H8 control: apply still gates a clean season; another sid never blocks."""
    root, season = _write_proj(tmp_path, SEASON_S1)
    evolve.apply(root, season)  # no reject-s1 record: the lint gate alone decides
    akar.append_record(root, "reject-s9", "other season rejected", "not this one")
    evolve.apply(root, season)  # reject-s9 resolves by exact id, never blocks s1


def test_rollback_active_season_stops_agents_before_record(tmp_path, monkeypatch):
    """H8 pin: rollback of an active season stops it before recording.

    Two marker stubs run; rollback_season must stop the season first
    (engine.stop_season, this caller's thread) and only then move the yaml
    and append rollback-s1. The call log proves the order: exactly
    ["stop", "record"]. Red today: rollback_season never stops anything,
    so the stubs outlive the record and the season stays running.
    """
    import signal
    import threading
    from contextlib import suppress

    sdir = tmp_path / "proj" / ".rumpun" / "rimba" / "s1"
    project = RUMPUN_YAML_STOP_TEMPLATE.format(
        w1_marker=str(sdir / "w1" / "started.marker"),
        w2_marker=str(sdir / "w2" / "started.marker"),
    )
    root, season = _write_proj(tmp_path, SEASON_STOP, project_yaml=project)

    calls: list[str] = []
    real_stop = engine.stop_season
    real_append = akar.append_record

    def spy_stop(r, s):
        calls.append("stop")
        return real_stop(r, s)

    def spy_append(*args, **kwargs):
        calls.append("record")
        return real_append(*args, **kwargs)

    monkeypatch.setattr(engine, "stop_season", spy_stop)
    monkeypatch.setattr(akar, "append_record", spy_append)

    def run_season():
        engine.start_season(season, root)

    starter = threading.Thread(target=run_season, daemon=True)
    starter.start()
    w1_marker = sdir / "w1" / "started.marker"
    w2_marker = sdir / "w2" / "started.marker"
    deadline = time.time() + 15
    while not (w1_marker.is_file() and w2_marker.is_file()):
        assert time.time() < deadline, "stubs never started"
        time.sleep(0.05)
    try:
        record = evolve.rollback_season(root, "s1")
        starter.join(15)
        assert not starter.is_alive()  # the watcher settled once the stop landed
        final = engine._load_state(root, "s1")
        assert final is not None and final["status"] == "stopped_operator"
        for name in ("w1", "w2"):
            meta_path = sdir / name / "state.json"
            assert meta_path.is_file()
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            assert (sdir / name / "started.marker").is_file(), f"{name} ran, no marker"
            assert not engine._alive(meta["pid"], meta["proc_start"]), (
                f"{name} outlived the rollback"
            )
        assert not season.exists()
        assert (root / "musim" / "rejected" / "s1.yaml").is_file()
        text = record.read_text(encoding="utf-8")
        assert "rollback-s1" in text
        assert calls == ["stop", "record"], f"ordered stop-then-record, got {calls}"
    finally:
        if starter.is_alive():
            real_stop(root, "s1")
            starter.join(10)
        for name in ("w1", "w2"):
            meta_path = sdir / name / "state.json"
            if not meta_path.is_file():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if engine._alive(meta["pid"], meta["proc_start"]):
                with suppress(OSError):
                    os.killpg(meta["pid"], signal.SIGKILL)


def test_start_refuses_rejected_season_yaml(tmp_path):
    """H8 pin: season start refuses a yaml outside musim/ canonical placement.

    reject_draft moves the draft to musim/rejected/ and records reject-s1;
    starting the moved file must raise EngineError and create no season
    state. Red today: the reviewer started a rejected file from that
    directory and it ran.
    """
    root, season = _write_proj(tmp_path, SEASON_S1, project_yaml=RUMPUN_YAML_DUAL)
    evolve.reject_draft(root, season)
    with pytest.raises(engine.EngineError):
        engine.start_season(root / "musim" / "rejected" / "s1.yaml", root)
    assert not (root / "rimba" / "s1" / "_season" / "state.json").is_file()


def test_start_error_mid_spawn_leaves_no_live_untracked_child(tmp_path):
    """H5 pin: a mid-spawn route failure raises AND leaves no live untracked child.

    w1's stub route exists; w2's route is missing from rumpun.yaml routes,
    so start_season aborts after spawning w1. The invariant: the error
    reaches the caller, and every stub that ran is registered (workspace
    state.json exists) and dead. Red today: w1 outlives the abort as a
    watcher-less child. The marker stub makes ran-versus-never-ran a file
    check, never a wall-clock wait.
    """
    import signal
    from contextlib import suppress

    sdir = tmp_path / "proj" / ".rumpun" / "rimba" / "s1"
    project = RUMPUN_YAML_H5.format(w1_marker=str(sdir / "w1" / "started.marker"))
    root, season = _write_proj(tmp_path, SEASON_STOP, project_yaml=project)
    try:
        with pytest.raises(engine.EngineError):
            engine.start_season(season, root)
        for name in ("w1", "w2"):
            ws = sdir / name
            meta_path = ws / "state.json"
            if not meta_path.is_file():
                # never admitted: if its marker exists anyway, it ran untracked
                assert not (ws / "started.marker").is_file(), f"{name} ran untracked"
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            assert not engine._alive(meta["pid"], meta["proc_start"]), (
                f"{name} outlived the startup abort"
            )
    finally:
        for name in ("w1", "w2"):
            meta_path = sdir / name / "state.json"
            if not meta_path.is_file():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if engine._alive(meta["pid"], meta["proc_start"]):
                with suppress(OSError):
                    os.killpg(meta["pid"], signal.SIGKILL)


def test_agent_budget_deadline_is_per_agent(tmp_path):
    """H9 pin: the short-budget benih is cut at its OWN deadline; the sibling completes.

    short carries minutes 0.05 (3s) and sleeps far past it; long carries
    minutes 10 and finishes its work in ~8s. Today the season deadline is
    max(short, long) = 600s, so nothing stops short within the window and
    start_season never settles: the join times out and the pin fails. With
    per-agent budgets, short is terminated (~3s), long exits 0 (~8s), and
    the season settles with short=terminated, long=exited 0.
    """
    import signal
    import threading
    from contextlib import suppress

    sdir = tmp_path / "proj" / ".rumpun" / "rimba" / "s1"
    project = RUMPUN_YAML_BUDGET.format(
        short_marker=str(sdir / "short" / "started.marker"),
        long_marker=str(sdir / "long" / "done.marker"),
    )
    root, season = _write_proj(tmp_path, SEASON_BUDGET, project_yaml=project)
    outcome: dict = {}

    def run_season():
        try:
            outcome["state"] = engine.start_season(season, root)
        except Exception as exc:  # re-raised below; never swallowed
            outcome["error"] = exc

    starter = threading.Thread(target=run_season, daemon=True)
    starter.start()
    try:
        starter.join(45)
        if starter.is_alive():
            pytest.fail(
                "season never settled in 45s: the short-budget agent was not "
                "terminated at its own deadline"
            )
        if "error" in outcome:
            raise outcome["error"]
        state = outcome["state"]
        assert state["status"] != "running"
        snaps = state["agents"]
        assert snaps["long"]["state"] == "exited"
        assert snaps["long"]["exit_code"] == 0
        assert (sdir / "long" / "done.marker").is_file(), (
            "the long-budget sibling did not complete its work"
        )
        assert snaps["short"]["state"] == "terminated"
        meta = json.loads(
            (sdir / "short" / "state.json").read_text(encoding="utf-8")
        )
        assert not engine._alive(meta["pid"], meta["proc_start"])
    finally:
        if starter.is_alive():
            engine.stop_season(root, "s1")
            starter.join(10)
        for name in ("short", "long"):
            meta_path = sdir / name / "state.json"
            if not meta_path.is_file():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if engine._alive(meta["pid"], meta["proc_start"]):
                with suppress(OSError):
                    os.killpg(meta["pid"], signal.SIGKILL)


# --- s21 w2: spec-first pins (codex-review-2026-09-14 M3, M11) ----------------
# RED against the s21 base code by design: w1's harvest.py/routes.py work
# turns the failing clauses green at integration. The measured red set is
# recorded in .rumpun/rimba/s21/w2/notes.md.


def test_harvest_writes_season_verdict_row_and_report_renders_win(tmp_path):
    """M3 pin: harvest_season writes the season verdict where reports read it.

    After harvest_season(...) on a completed WIN season, rimba/<sid>/
    verdicts.jsonl carries exactly one season-level WIN row (the row rule
    report._verdict_of reads: row["season"] == sid), and the rendered season
    report shows WIN in its verdict headline. Red at s21 base: harvest only
    appends the akar record; rimba/<sid>/verdicts.jsonl is never written.
    """
    _write_season_state(tmp_path)
    harvest.harvest_season(tmp_path, "s1", "WIN", "note")
    verdicts = tmp_path / "rimba" / "s1" / "verdicts.jsonl"
    assert verdicts.is_file(), "harvest must write rimba/<sid>/verdicts.jsonl"
    rows = [
        json.loads(line)
        for line in verdicts.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    season_rows = [row for row in rows if row.get("season") == "s1"]
    assert len(season_rows) == 1, f"expected one season-level row, got: {rows}"
    assert season_rows[0]["verdict"] == "WIN"
    doc = report.render_report(tmp_path, "s1")
    html = doc.read_text(encoding="utf-8")
    start = html.find('<p class="one">')
    assert start != -1, "season report verdict headline missing"
    end = html.find("</p>", start)
    assert end != -1, "season report verdict headline unterminated"
    assert "WIN" in html[start:end], "report headline does not render WIN"


def test_second_harvest_refuses_and_keeps_single_record(tmp_path):
    """M4-minimal pin: a second harvest_season on one season refuses.

    akar refuses the duplicate <sid>-harvest record id (serialized append,
    s18 H6), so the second call raises akar.AkarError and exactly one
    harvest record remains in the ledger. Green at s21 base: measured below,
    the refusal already holds; the pin guards it through the M3 change.
    """
    _write_season_state(tmp_path)
    harvest.harvest_season(tmp_path, "s1", "WIN", "note")
    with pytest.raises(akar.AkarError):
        harvest.harvest_season(tmp_path, "s1", "WIN", "note")
    records = list((tmp_path / "akar").glob("*_s1-harvest.md"))
    assert len(records) == 1


def test_write_routes_commands_spawn_clean(tmp_path):
    """M11 pin: write_routes generates spawn-clean commands, scaffold intact.

    Every command write_routes writes into a scaffolded rumpun.yaml contains
    no "<model>" placeholder and, with {prompt} resolved, passes /bin/sh -n.
    The rest of the scaffold survives the patch and the file still parses.
    Red at s21 base: the claude login route is generated with a literal
    --model <model> placeholder (the defect fixed ad hoc in the campaign
    copy at s15 lives on in the generator).
    """
    target = tmp_path / "proj"
    scaffold.init_project(target)
    cfg = target / ".rumpun" / "rumpun.yaml"
    before = cfg.read_text(encoding="utf-8").splitlines()
    count = routes.write_routes(cfg)
    assert count >= 1
    commands = list(
        (yaml.safe_load(cfg.read_text(encoding="utf-8")).get("routes") or {}).values()
    )
    assert commands, "write_routes wrote no route commands"
    offenders = [cmd for cmd in commands if "<model>" in cmd]
    assert offenders == [], f"<model> placeholder still generated: {offenders}"
    for cmd in commands:
        proc = subprocess.run(
            ["/bin/sh", "-n"],
            input=cmd.replace("{prompt}", "prompt.md"),
            text=True,
            capture_output=True,
        )
        assert proc.returncode == 0, f"/bin/sh -n rejected: {cmd}\n{proc.stderr}"
    after = cfg.read_text(encoding="utf-8").splitlines()
    kept = [line for line in before if not line.startswith("routes:")]
    it = iter(after)
    assert all(line in it for line in kept), "write_routes disturbed the scaffold"


# --- s22 w2: lane integrity pins (codex-review-2026-09-14 M1, M5, M6, M7) ---

RUMPUN_YAML_FAIL = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "false"
"""


def test_collab_append_event_rejects_reserved_keys(tmp_path):
    """M6 pin: harness fields are authoritative; the contract is REJECT.

    A payload carrying seq, from, or ts raises LaneError and writes nothing.
    A clean payload still appends with harness-assigned seq and from, so a
    forged value can never reach the file through the payload.
    """
    lane = collab.prepare_lane(tmp_path, "s1", "dev")
    for forged in ({"seq": 99, "from": "forged"}, {"seq": 5}, {"from": "x"}, {"ts": 1.5}):
        with pytest.raises(collab.LaneError):
            collab.append_event(lane, "w1", forged)
    assert collab.read_events(lane) == []
    kept = collab.append_event(lane, "w1", {"text": "clean"})
    assert kept["seq"] == 0 and kept["from"] == "w1"


def test_collab_reader_never_observes_partial_row_during_appends(tmp_path):
    """M7 pin: a reader never parses a partial row while an append is in flight.

    Deterministic shape: the test plays the writer mid-append — it holds the
    lane's LOCK_EX, leaves a partial row (no terminator) on disk, then
    releases a barrier into a reader thread. The locked reader (s22
    contract) blocks on LOCK_SH until the append completes and then replays
    clean; the old unlocked reader parses the partial tail immediately and
    dies on LaneError inside the observation window. The held lock makes the
    pin structural, not a scheduler race.
    """
    import threading

    lane = collab.prepare_lane(tmp_path, "s1", "dev")
    collab.append_event(lane, "w", {"i": 0})
    partial = b'{"blob": "' + b"x" * 524288
    outcomes: list = []
    barrier = threading.Barrier(2)

    def reader():
        barrier.wait()
        try:
            outcomes.append(("ok", len(collab.read_events(lane))))
        except Exception as exc:  # any reader death is a pin red
            outcomes.append(("error", exc))

    rt = threading.Thread(target=reader)
    rt.start()
    with open(lane["lock"], "a") as probe:
        fcntl.flock(probe.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with open(lane["file"], "ab") as fh:
            fh.write(partial)
        barrier.wait()  # reader now reads against the in-flight append
        time.sleep(0.3)
        assert rt.is_alive() and not outcomes, (
            f"reader did not block behind the append lock; observed: {outcomes}"
        )
        with open(lane["file"], "ab") as fh:
            fh.write(b'"}\n')  # the append completes: terminator lands
    rt.join(30)
    assert not rt.is_alive()
    assert outcomes == [("ok", 2)]


def test_collab_append_event_recovers_partial_tail(tmp_path, caplog):
    """M7 pin: a hand-crafted partial tail is recovered on the next append.

    The tail (invalid JSON, no trailing newline) is truncated under the
    exclusive lock; the log carries the recovered byte count, never the
    content; subsequent reads replay only clean rows.
    """
    import re

    lane = collab.prepare_lane(tmp_path, "s1", "dev")
    collab.append_event(lane, "w1", {"text": "first"})
    collab.append_event(lane, "w2", {"text": "second"})
    fragment = b'{"seq": 2, "from": "w9", "text": "partial-trunc'
    with Path(lane["file"]).open("ab") as fh:
        fh.write(fragment)
    with caplog.at_level(logging.INFO):
        e2 = collab.append_event(lane, "w1", {"text": "after-crash"})
    assert e2["seq"] == 2
    events = collab.read_events(lane)
    assert [e["seq"] for e in events] == [0, 1, 2]
    assert events[-1]["text"] == "after-crash"
    assert events[-1]["from"] == "w1"
    with Path(lane["file"]).open("rb") as fh:
        raw = fh.read()
    assert raw.endswith(b"\n")
    assert b"partial-trunc" not in raw
    messages = [r.getMessage() for r in caplog.records]
    assert any(re.search(r"recovered \d+ bytes", m) for m in messages), messages
    assert all("partial-trunc" not in m for m in messages)


def test_report_running_season_render_deterministic_links_sorted(tmp_path):
    """M1 pin (w1's patch): rendering a running season twice from unchanged
    persisted bytes is byte-identical, and workspace links are sorted."""
    import re

    root, _season = _write_proj(tmp_path, SEASON_S1)
    ws = root / "rimba" / "s1" / "w1"
    ws.mkdir(parents=True)
    (ws / "state.json").write_text(
        json.dumps(
            {
                "name": "w1",
                "route": "glm",
                "cmd": "x",
                "pid": 1,
                "proc_start": 987654321,
                "started_at": 1000.0,
            }
        ),
        encoding="utf-8",
    )
    (ws / "agent.log").write_text("stream\n", encoding="utf-8")
    (ws / "z_deliverable.md").write_text("z\n", encoding="utf-8")
    (ws / "a_dir").mkdir()
    (ws / "a_dir" / "m_file.md").write_text("m\n", encoding="utf-8")
    state = root / "rimba" / "s1" / "_season"
    state.mkdir(parents=True)
    (state / "state.json").write_text(
        json.dumps(
            {
                "id": "s1",
                "status": "running",
                "started_at": 1000.0,
                "stall_s": 2700.0,
                "spawned": {"w1": {"pid": 1, "engine_proc_start": 987654321}},
            }
        ),
        encoding="utf-8",
    )
    first = report.render_report(root, "s1")
    first_bytes = first.read_bytes()
    time.sleep(0.35)
    second = report.render_report(root, "s1")
    second_bytes = second.read_bytes()
    assert first_bytes == second_bytes, "two renders of unchanged bytes differ"
    hrefs = re.findall(r'href="w1/([^"]+)"', first_bytes.decode("utf-8"))
    assert hrefs == sorted(hrefs), f"workspace links unsorted: {hrefs}"


def test_season_all_agents_failed_maps_to_nonzero(tmp_path):
    """M5 pin (w1's patch): a both-agents-fail season finalizes with an
    honest status ("failed") and the season start verb maps it to a nonzero
    exit, so shell automation cannot advance on universal agent failure."""
    root, season = _write_proj(tmp_path, SEASON_DUAL, project_yaml=RUMPUN_YAML_FAIL)
    proc = subprocess.run(
        [sys.executable, "-m", "rumpun", "season", "start", str(season)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(tmp_path),
    )
    assert proc.returncode != 0, (
        f"season start exited 0 with both agents failed; stderr:\n{proc.stderr}"
    )
    state = json.loads(
        (root / "rimba" / "s1" / "_season" / "state.json").read_text(encoding="utf-8"),
    )
    assert state["status"] == "failed"
    agents = state.get("agents") or {}
    assert {n: (agents.get(n) or {}).get("state") for n in ("alpha", "beta")} == {
        "alpha": "failed",
        "beta": "failed",
    }


# --- s23 w2: M9 domain errors + M10 trade-off pin + M2/M8 pins (spec-first) ----
#
# M9 lands in this workspace's lint.py/yamlio.py copies (the harness merges
# them); M2 (audit) and M8 (evolve) are spec-first for w1's patches; M10 pins
# the accepted s15 hot-fix trade-off and is green by design. Red against the
# current tree is expected for the M2/M8/M9 pins; the measured set lives in
# this workspace's notes.md. Pinned contracts:
# - lint: container-type checks run BEFORE traversal — the season document,
#   methodology, each methodology.pipeline node, each benih entry, each
#   benih's budget block, stop, and rumpun.yaml autonomy must be mappings;
#   violations are error findings whose messages name the path (methodology,
#   methodology.pipeline[i], benih[i]) — never AttributeError/TypeError.
# - yamlio: non-string keys are rejected at any depth (sequences recurse;
#   the message names the path, file.benih[0] style) and unhashable seq/map
#   keys raise YamlError instead of escaping construction as TypeError;
#   valid documents still parse.
# - M2 (w1's audit.py): a declared phase whose writes artifact exists in
#   every completed season declaring the phase yields NO dead-phase
#   candidate; each phase's denominator counts only completed seasons
#   declaring the phase (with the same phase -> writes contract).
# - M8 (w1's evolve.py): after rejecting the latest season, drafting never
#   reuses its id — either a fresh s<N+1> lands or the draft is refused
#   without recreating the rejected id.
# - M10 (accepted trade-off, akar stall-rule-fired-on-runtime): mtime-only
#   progress counts as progress, so touch-only activity keeps a live spawn
#   "running" until its budget stops it. Green by design (documents the
#   decision; DESIGN 13 quote in the test docstring).


def _m9_season(methodology_block: str) -> str:
    """SEASON_S1 with the methodology..benih segment replaced; benih kept."""
    head, rest = SEASON_S1.split("methodology:", 1)
    _body, tail = rest.split("benih:", 1)
    return head + methodology_block + "\nbenih:" + tail


def test_lint_methodology_null_is_domain_error(tmp_path):
    """M9 pin: methodology: null is an error finding naming the path.

    Red today: lint records 'methodology.approach is required' then calls
    .get on None — the reviewer's uncaught AttributeError.
    """
    season_text = _m9_season("methodology: null")
    _root, season = _write_proj(tmp_path, season_text)
    findings = lint.lint(season)
    hits = [
        f.message
        for f in findings
        if f.severity == "error" and "methodology" in f.message
    ]
    assert hits, f"no domain error for methodology: {[f.message for f in findings]}"


def test_lint_pipeline_string_node_is_domain_error(tmp_path):
    """M9 pin: a string pipeline node is a domain error naming the path.

    Red today: phases = [n.get("phase") for n in pipeline] crashes with
    AttributeError on the string entry before any per-node check runs.
    """
    season_text = _m9_season(
        'methodology:\n  approach: "x"\n  evidence: []\n  pipeline:\n    - execute'
    )
    _root, season = _write_proj(tmp_path, season_text)
    findings = lint.lint(season)
    hits = [
        f.message
        for f in findings
        if f.severity == "error" and "methodology.pipeline[0]" in f.message
    ]
    assert hits, f"no domain error for the string node: {[f.message for f in findings]}"


def test_lint_benih_list_entry_is_domain_error(tmp_path):
    """M9 pin: a benih entry that is a list is a domain error naming the path.

    Red today: the per-benih loop calls b.get on the [w1] entry —
    AttributeError.
    """
    season_text = SEASON_S1.replace(
        "- name: w1\n    route: glm\n    prompt: prompts/dev/dummy.md\n"
        "    knowledge: none\n    budget: {minutes: 1}",
        "- [w1]",
    )
    _root, season = _write_proj(tmp_path, season_text)
    findings = lint.lint(season)
    hits = [
        f.message for f in findings if f.severity == "error" and "benih[0]" in f.message
    ]
    assert hits, f"no domain error for the benih entry: {[f.message for f in findings]}"


def test_yamlio_rejects_non_string_key_inside_sequence(tmp_path):
    """M9 pin: a non-string key inside a sequence is rejected, naming the path.

    Red today: the key check recurses dicts only, so benih[0]'s numeric key
    parses clean — the advertised contract leaks at nested depth.
    """
    doc = "id: s1\nbenih:\n  - name: w1\n    2: trap\n"
    path = tmp_path / "season.yaml"
    path.write_text(doc, encoding="utf-8")
    with pytest.raises(yamlio.YamlError, match=r"benih\[0\]"):
        yamlio.load(path)


def test_yamlio_unhashable_key_is_yaml_error_not_type_error(tmp_path):
    """M9 pin: a YAML seq/map key raises YamlError, never the raw TypeError.

    Red today: the duplicate-check membership test on an unhashable key
    escapes construction as TypeError before any domain error can be
    raised.
    """
    doc = "? [a, b]\n: value\n"
    path = tmp_path / "seq-key.yaml"
    path.write_text(doc, encoding="utf-8")
    with pytest.raises(yamlio.YamlError):
        yamlio.load(path)


def test_yamlio_valid_document_still_parses(tmp_path):
    """M9 control: the containment fix rejects nothing valid.

    The full SEASON_S1 parses; the quoted "on" key stays a string key at
    its nested depth.
    """
    path = tmp_path / "season.yaml"
    path.write_text(SEASON_S1, encoding="utf-8")
    doc = yamlio.load(path)
    assert isinstance(doc, dict)
    assert list(doc["stop"].keys()) == ["on"]
    assert doc["methodology"]["pipeline"][0]["phase"] == "execute"


def test_audit_custom_artifact_present_everywhere_no_dead_phase(tmp_path):
    """M2 pin (w1's patch): no dead-phase candidate for a declared custom
    artifact present in every completed season declaring the phase.

    Red today: artifact discovery scans the fixed LEDGER_ARTIFACTS set, so
    custom.jsonl reads 0-of-N and proposes trimming a live phase; the
    denominator also counts unfinished seasons (s3, running) and seasons
    predating the phase (s1).
    """
    enrich = (
        "    - phase: enrich\n"
        "      primitive: execute\n"
        "      agents: benih\n"
        "      prompt: prompts/dev/dummy.md\n"
        "      writes: custom.jsonl\n"
        "benih:"
    )
    root = _write_audit_proj(tmp_path, sids=("s1", "s2", "s3"))
    for sid in ("s2", "s3"):
        (root / "musim" / f"{sid}.yaml").write_text(
            AUDIT_SEASON.format(sid=sid).replace("benih:", enrich), encoding="utf-8"
        )
    _write_rimba_season(root, "s1")  # completed; declares execute only
    _write_rimba_season(root, "s2")  # completed; declares execute + enrich
    _write_rimba_season(root, "s3", status="running")  # unfinished: never counts
    for sid in ("s1", "s2", "s3"):
        (root / "rimba" / sid / "custom.jsonl").write_text(
            '{"custom": 1}\n', encoding="utf-8"
        )
    text = audit.run_audit(root).read_text(encoding="utf-8")
    assert not any("exercise or trim" in line for line in text.splitlines()), text
    assert "wrote its artifact in 2 of 2" in text  # execute: s1+s2 completed
    assert any(
        "enrich" in line and "wrote its artifact in 1 of 1" in line
        for line in text.splitlines()
    )


def test_draft_after_rejecting_latest_never_reuses_id(tmp_path):
    """M8 pin (w1's patch): reject the latest season, then draft — no id reuse.

    Red today: draft numbering scans top-level musim/s*.yaml only, so after
    s2 moves to musim/rejected/, drafting from s1 mints s2 again.
    """
    root, s1 = _write_proj(tmp_path, SEASON_S1)
    s2 = root / "musim" / "s2.yaml"
    s2.write_text(SEASON_S1.replace("id: s1\n", "id: s2\n"), encoding="utf-8")
    evolve.reject_draft(root, s2)
    assert (root / "musim" / "rejected" / "s2.yaml").is_file()
    try:
        drafted = evolve.draft_next(root, s1)
    except evolve.EvolveError:
        # A refusal is a valid no-reuse shape; it must not recreate the id.
        assert not (root / "musim" / "s2.yaml").exists()
        return
    assert drafted == root / "musim" / "s3.yaml"
    assert drafted.read_text(encoding="utf-8").startswith("# musim/s3.yaml")
    assert not (root / "musim" / "s2.yaml").exists()


def test_agent_snap_mtime_only_touch_counts_as_progress(tmp_path):
    """M10 pin: the accepted s15 hot-fix trade-off, pinned as-is.

    DESIGN 13 ratifies durable-progress stall keys: "Heartbeats, identical
    log lines, and mtime-only changes do not count." The s15 hot-fix (akar
    stall-rule-fired-on-runtime) keys stall on agent.log mtime growth,
    which ACCEPTS mtime-only progress: identical bytes touched fresh reset
    the stall clock, so touch-only activity keeps a live spawn "running"
    until its budget stops it. Pinned here as-is; content-based progress
    (changed artifact content, grace interval) is a candidate for a future
    season (notes.md).
    """
    ws = tmp_path / "w1"
    ws.mkdir()
    meta = {
        "name": "w1",
        "route": "glm",
        "pid": os.getpid(),
        "proc_start": engine._proc_start_ticks(os.getpid()),
        "started_at": time.time() - 3600.0,
    }
    (ws / "state.json").write_text(json.dumps(meta), encoding="utf-8")
    log = ws / "agent.log"
    log.write_text("identical\n", encoding="utf-8")
    assert engine._agent_snap(ws, stall_s=1.0)["state"] == "running"
    old = time.time() - 30.0
    os.utime(log, (old, old))
    assert engine._agent_snap(ws, stall_s=1.0)["state"] == "stalled"
    os.utime(log)  # touch: identical bytes, fresh mtime
    assert engine._agent_snap(ws, stall_s=1.0)["state"] == "running"


# --- s24 w2 pins (spec-first): content-based progress + harvest row fields -----
#
# Spec-first (musim/s24.yaml): the progress pins run red against the current
# tree (mtime rule) and green once w1's content-based patch lands. Measured
# red set + per-test contract: this season's w2 workspace notes.md. Pinned:
# - Progress keys on appended bytes (content), never mtime: the watcher scan
#   stamps a fresh progress time when agent.log grew past its last
#   observation; a log only touched (mtime bumped, size unchanged) never
#   stamps. _agent_snap judges live spawns on the stamp (fallback
#   started_at). This closes the s23 M10 touch trade-off; w1's patch is
#   expected to flip the s23 pin test_agent_snap_mtime_only_touch_counts_as
#   _progress at merge.
# - The M10 trade-off comment references the content-based rule (the s23
#   decision text moved).
# - Season verdict rows carry caller-supplied band/observed, and the cli
#   harvest verb passes --band/--observed through; without the flags both
#   stay "".
# Additions-only: the 117 existing tests are untouched.


def _s24_stub(ws: Path, name: str) -> None:
    """Live stub workspace root/rimba/s1/<name>: meta + a one-line base log.

    Same meta shape and elapsed hour as the s15/s23 stall pins; the rimba
    nesting lets _scan_agent_stream derive the season lock from ws.
    """
    ws.mkdir(parents=True)
    meta = {
        "name": name,
        "route": "fable",
        "pid": os.getpid(),
        "proc_start": engine._proc_start_ticks(os.getpid()),
        "started_at": time.time() - 3600.0,
    }
    (ws / "state.json").write_text(json.dumps(meta), encoding="utf-8")
    (ws / "agent.log").write_text("identical\n", encoding="utf-8")


def _scan(ws: Path) -> None:
    """One watcher-cycle scan: re-read ws state.json, hand it to the engine."""
    meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    engine._scan_agent_stream(ws, meta)


def _last_verdict_row(root: Path, sid: str) -> dict:
    """The season-level row harvest writes into rimba/<sid>/verdicts.jsonl."""
    path = root / "rimba" / sid / "verdicts.jsonl"
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return json.loads(lines[-1])


def test_agent_snap_appended_bytes_are_progress_stale_mtime(tmp_path):
    """Appended bytes are running however stale the log mtime is.

    s24 pin, red against the mtime rule: the scan re-baselines agent.log,
    bytes are appended, the mtime is forced stale, and a second scan
    observes the growth. The snap must read running off the observed
    growth -- never off mtime. Same elapsed hour and 1s window as the
    touch stub below.
    """
    ws = tmp_path / "rimba" / "s1" / "w1"
    _s24_stub(ws, "w1")
    _scan(ws)
    with (ws / "agent.log").open("ab") as fh:
        fh.write(b"more\n")
    old = time.time() - 30.0
    os.utime(ws / "agent.log", (old, old))
    _scan(ws)
    assert engine._agent_snap(ws, stall_s=1.0)["state"] == "running"


def test_agent_snap_touch_only_is_stalled_despite_fresh_mtime(tmp_path):
    """A touched-only log (fresh mtime, unchanged bytes) stalls past the window.

    s24 pin, red against the mtime rule: same base log, elapsed hour, and
    window as the growth stub; only the mtime moves. The scan sees no
    growth, so the snap must call the spawn stalled despite the fresh
    mtime -- closing the M10 touch trade-off (DESIGN 13: mtime-only
    changes do not count).
    """
    ws = tmp_path / "rimba" / "s1" / "w2"
    _s24_stub(ws, "w2")
    _scan(ws)
    os.utime(ws / "agent.log")  # touch: identical bytes, fresh mtime
    _scan(ws)
    assert engine._agent_snap(ws, stall_s=1.0)["state"] == "stalled"


def test_m10_comment_references_content_based_rule():
    """The M10 trade-off comment documents the content-based rule.

    s24 pin, red against the current tree: the s23 comment calls progress
    mtime-based and defers the content-based rule to a future season. With
    the s24 rule the decision text must reference content-based progress
    (grep via inspect, so the comment may sit anywhere in engine.py): an
    M10 marker whose window names content without the old mtime-based
    wording, and the moved s23 sentence gone.
    """
    source = inspect.getsource(engine)
    lines = source.splitlines()
    m10 = [i for i, line in enumerate(lines) if "M10" in line]
    assert m10, "the M10 trade-off comment must stay in engine.py"
    windows = ["\n".join(lines[max(0, i - 8): i + 9]).lower() for i in m10]
    assert any("content" in w and "mtime-based" not in w for w in windows), source
    assert "touching agent.log without writing content defeats" not in source


def test_harvest_season_row_carries_band_and_observed(tmp_path):
    """harvest_season writes caller-supplied band/observed into the row.

    s24 pin, function level (green against the current tree: the kwargs
    exist; the CLI pin below is the red half): band and observed are
    verdict content [A] and must reach the M3 single verdict book
    non-empty when supplied.
    """
    _write_season_state(tmp_path)
    harvest.harvest_season(
        tmp_path, "s1", "WIN", "note", band="4 of 5 clauses", observed="suite 117/117",
    )
    row = _last_verdict_row(tmp_path, "s1")
    assert row["band"] == "4 of 5 clauses"
    assert row["observed"] == "suite 117/117"


def test_cli_harvest_passes_band_and_observed_through(tmp_path, monkeypatch):
    """The harvest verb passes --band/--observed into the season row.

    s24 pin, red against the current tree: the verb has no --band or
    --observed flags, so argparse exits 2 on them today. Contract:
    cli.main(["harvest", id, --verdict, --implies, --band, --observed])
    exits 0 and the row carries both values verbatim.
    """
    (tmp_path / ".rumpun").mkdir()
    (tmp_path / ".rumpun" / "rumpun.yaml").write_text(RUMPUN_YAML, encoding="utf-8")
    _write_season_state(tmp_path / ".rumpun")
    monkeypatch.chdir(tmp_path)
    rc = cli.main([
        "harvest", "s1", "--verdict", "WIN", "--implies", "note",
        "--band", "4 of 5 clauses", "--observed", "results.jsonl row",
    ])
    assert rc == 0
    row = _last_verdict_row(tmp_path / ".rumpun", "s1")
    assert row["band"] == "4 of 5 clauses"
    assert row["observed"] == "results.jsonl row"


def test_cli_harvest_without_flags_leaves_band_observed_empty(tmp_path, monkeypatch):
    """Without --band/--observed the row carries both as empty strings.

    s24 pin, green against the current tree (harvest_season defaults both
    to "" and the verb omits them): the flags are optional and their
    absence must not change the row shape.
    """
    (tmp_path / ".rumpun").mkdir()
    (tmp_path / ".rumpun" / "rumpun.yaml").write_text(RUMPUN_YAML, encoding="utf-8")
    _write_season_state(tmp_path / ".rumpun")
    monkeypatch.chdir(tmp_path)
    rc = cli.main(["harvest", "s1", "--verdict", "WIN", "--implies", "note"])
    assert rc == 0
    row = _last_verdict_row(tmp_path / ".rumpun", "s1")
    assert row["band"] == ""
    assert row["observed"] == ""




# --- s25 w2: replay-matrix regression pin ---------------------------------
# The s25 w1 corpus runner (tools/replay_corpus.py) replays the akar
# evidence scripts (ratified s17-s24 behavior) against the current repo and
# emits a markdown matrix: script | verdict | first failing line | note.
# This pin makes that matrix executable evidence: a historical repro that
# marks current main regressed goes red here, not only in a season
# workspace. Taxonomy note: the runner never emits a literal REGRESSION
# verdict token -- a regression appears as a FAIL row whose note names it
# ("REGRESSION candidate (fix landed on main)" or the h6 race hint), so
# both spellings are checked. SKIP rows (including UNCLASSIFIED skips) are
# allowed per the s25 deliverable; DRIFT and plain FAIL rows are not pin
# failures (DRIFT records an aged script assumption; plain FAIL is runner
# adaptation debt argued in the matrix note column).

def _replay_matrix_rows(repo: Path) -> dict[str, str]:
    """Run the runner once and parse (script -> verdict, note) from the matrix.

    Missing runner, nonzero runner exit, or a missing/unparseable matrix is
    a pin failure, never a skip. Cell splitting respects the runner's
    escaped pipes ("\\|").
    """
    runner = repo / "tools" / "replay_corpus.py"
    if not runner.is_file():
        pytest.fail(
            "tools/replay_corpus.py is missing: the s25 replay pin has no "
            "runner to execute (the matrix is executable evidence only when "
            "the runner runs)"
        )
    proc = subprocess.run(
        [sys.executable, str(runner)],
        cwd=str(repo),
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert proc.returncode == 0, (
        f"replay runner exited {proc.returncode}; "
        f"stdout tail: {proc.stdout[-2000:]}; stderr tail: {proc.stderr[-2000:]}"
    )
    candidates = [
        repo / "replay-matrix.md",  # runner default out-dir: tools/..
        repo / "tools" / "replay-matrix.md",
        repo / ".rumpun" / "akar" / "evidence" / "replay-matrix.md",
    ]
    if (repo / "tools").is_dir():
        candidates += sorted((repo / "tools").glob("replay-matrix.md"))
    matrix = next((p for p in candidates if p.is_file()), None)
    if matrix is None:
        pytest.fail("runner left no replay-matrix.md under tools/ or evidence/")
    rows: dict[str, tuple[str, str]] = {}
    for line in matrix.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) >= 2 and cells[0] and cells[0] != "script":
            verdict = cells[1].strip("*`_ ").split()[0] if cells[1] else ""
            if verdict in {"PASS", "FAIL", "DRIFT", "REGRESSION", "SKIP"}:
                rows[cells[0]] = (verdict, cells[3] if len(cells) >= 4 else "")
    if not rows:
        pytest.fail(f"no verdict rows parsed from {matrix}")
    out: dict[str, str] = {}
    for script, (verdict, note) in rows.items():
        out[script] = (
            verdict if verdict in {"PASS", "SKIP"} else f"{verdict} ({note})"
        )
    return out


def test_replay_matrix_has_no_regressions():
    """s25 w2 pin: no REGRESSION verdicts in the s25 replay matrix.

    Runs the corpus runner end to end (its per-script subprocess isolation
    and cleanup are the runner's contract) and parses the emitted matrix.
    SKIP rows are allowed; REGRESSION fails under both spellings: a literal
    REGRESSION verdict token, or w1's FAIL row whose note names the
    regression ("REGRESSION candidate ...").
    """
    repo = Path(__file__).resolve().parents[1]
    rows = _replay_matrix_rows(repo)
    regressions = {
        script: verdict
        for script, verdict in rows.items()
        if verdict == "REGRESSION" or (
            verdict.startswith("FAIL") and "REGRESSION" in verdict
        )
    }
    assert not regressions, (
        "replay matrix carries REGRESSION verdicts (ratified repros vs "
        f"main): {regressions}; matrix: replay-matrix.md at the repo root"
    )


# --- s26 w2: corpus-matrix ingestion pins (spec-first, red pre-merge) -------
# The corpus gate (s25, tools/replay_corpus.py) emits the one ledger artifact
# that can show a main-line regression, and reflection never reads it:
# audit-13 and audit-14 both armed zero candidates while the matrix sat in
# evidence. The s26 contract these pins ratify:
# - run_audit ingests the newest replay-matrix.md under akar evidence
#   (newest = highest evidence season, mtime as the pin's tiebreak aid);
# - a FAIL row (the runner's regression spelling) or a literal REGRESSION
#   verdict token arms ONE "corpus regression" candidate citing the script
#   and first failing line, placed FIRST among candidates, with
#   MAX_CANDIDATES still capping the total;
# - an all-green matrix (>= 1 PASS row, zero FAIL) yields the plain
#   "corpus: N repro scripts green" finding, never a candidate;
# - with no matrix present, run_audit's output is byte-identical to the
#   pre-s26 body (GOLDEN_PRE_S26_BODY, captured not hand-written);
# - malformed data rows are skipped with one DEBUG log each, never crashing
#   the audit; header and separator rows are structure, not malformed data.


def _write_matrix(root, sid, rows, mtime=None):
    """One evidence matrix akar/evidence/<sid>/replay-matrix.md from tuples.

    rows are (script, verdict, first failing line, note) string tuples;
    shorter or garbled tuples pass through verbatim (malformed-row pins).
    mtime stamps the file so "newest" discovery is pin-deterministic.
    """
    directory = root / "akar" / "evidence" / sid
    directory.mkdir(parents=True, exist_ok=True)
    lines = [
        "# s26 w2 fixture matrix",
        "",
        "| script | verdict | first failing line | note |",
        "|---|---|---|---|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    path = directory / "replay-matrix.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


GOLDEN_PRE_S26_BODY = [
    "scope: last 2 musim seasons (s1,s2); engine seasons with rimba/ (2): s1,s2",
    "declared phases from latest season s2: execute->results.jsonl, "
    "evaluate->verdicts.jsonl",
    "F1 phase liveness: phase execute (writes results.jsonl) wrote its "
    "artifact in 1 of 2 engine seasons (s1,s2)",
    "F1 phase liveness: phase evaluate (writes verdicts.jsonl) wrote its "
    "artifact in 1 of 2 engine seasons (s1,s2)",
    "F2 stall recurrence: stopped_stall in 0 of 1 seasons with state.json "
    "(none); recurrence no (threshold 2)",
    "F3 verdict histogram over verdicts.jsonl of s1 (none in: s2): WIN 0, "
    "LOSS 0, INVALID 0",
    "F4 route outcomes: no finalized agent snapshots in audited engine "
    "seasons (s1,s2)",
    "F5 band calibration: no LOSS season shipped integrated modules (s1)",
    "F6 budget compliance: campaign_cost_cap unset since campaign start (P9) "
    "— operator sets the number; the tool only flags",
    "candidates: none — no trigger met; nothing proposed without evidence",
]


def test_audit_ingests_newest_evidence_matrix(tmp_path):
    """Pin: the newest replay-matrix.md under akar evidence is the input.

    Red today: run_audit never reads any matrix (the audit-13/14 blind
    spot). The corpus candidate must cite the s10 matrix's row only:
    evidence s10 outranks s9 numerically AND by mtime, so a lexicographic
    directory sort (which picks s9 first) is red under this fixture.
    """
    root = _audit_base(tmp_path)
    _write_matrix(
        root,
        "s9",
        [("s9/old.py", "FAIL", "assert old (line 3)", "REGRESSION candidate")],
        mtime=1_000_000,
    )
    _write_matrix(
        root,
        "s10",
        [("s10/new.py", "FAIL", "assert new (line 42)", "REGRESSION candidate")],
        mtime=2_000_000,
    )
    text = audit.run_audit(root).read_text(encoding="utf-8")
    candidates = [line for line in text.splitlines() if line.startswith("candidate:")]
    assert len(candidates) == 1
    assert "corpus regression" in candidates[0]
    assert "s10/new.py" in candidates[0]
    assert "assert new (line 42)" in candidates[0]  # cites first failing line
    assert "s9/old.py" not in text  # the older matrix is never ingested


def test_audit_corpus_candidate_first_under_cap(tmp_path):
    """Pins: regression candidate placed first; MAX_CANDIDATES still caps.

    Red today: no corpus candidate exists and the priority is phase ->
    route -> calibration. Post-s26 the FAIL row takes slot 1 ahead of the
    phase/route/calibration triggers and the cap holds: 4 triggered
    proposals -> 3 candidates with calibration demoted to the unproposed
    line.
    """
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2")
    latest = root / "musim" / "s2.yaml"
    latest.write_text(
        AUDIT_SEASON.format(sid="s2").replace(
            "      writes: verdicts.jsonl\n",
            "      writes: verdicts.jsonl\n"
            "    - phase: reflect\n"
            "      primitive: reflect\n"
            "      agents: benih\n"
            "      prompt: prompts/dev/dummy.md\n"
            "      writes: reflections.jsonl\n",
        ),
        encoding="utf-8",
    )
    for sid in ("s1", "s2"):
        _write_harvest_record(root, sid, "LOSS")
        _write_results_rows(root, sid, [{"integrated": True}])
        _write_spawn(root, sid, f"e-{sid}", "sol", "clean-empty")
    _write_matrix(
        root,
        "s10",
        [("s26/repro.py", "FAIL", "assert race (line 9)", "REGRESSION candidate")],
        mtime=2_000_000,
    )
    text = audit.run_audit(root).read_text(encoding="utf-8")
    candidates = [line for line in text.splitlines() if line.startswith("candidate:")]
    assert len(candidates) == 3  # the cap still applies with all triggers met
    assert "corpus regression" in candidates[0]
    assert "s26/repro.py" in candidates[0] and "assert race (line 9)" in candidates[0]
    assert "exercise or trim" in candidates[1]  # the phase trigger follows
    assert "tool-check" in candidates[2] and "sol" in candidates[2]
    assert not any("recalibrate" in line for line in candidates)
    dropped = [line for line in text.splitlines() if "unproposed here" in line]
    assert len(dropped) == 1 and "LOSS band calibration" in dropped[0]


def test_audit_all_green_matrix_is_finding_never_candidate(tmp_path):
    """Pin: an all-green matrix (>= 1 PASS row, zero FAIL) is a finding only.

    Red today: no corpus finding exists anywhere in run_audit's output.
    """
    root = _audit_base(tmp_path)
    _write_matrix(
        root,
        "s10",
        [
            ("s18/warn.py", "PASS", "--", "exit 0; all-pass signature matched"),
            ("s20/h5h9.py", "PASS", "--", "exit 0; all-pass signature matched"),
        ],
        mtime=2_000_000,
    )
    text = audit.run_audit(root).read_text(encoding="utf-8")
    candidates = [line for line in text.splitlines() if line.startswith("candidate:")]
    assert not candidates
    assert "candidates: none" in text  # the pre-s26 none-line stays
    findings = [line for line in text.splitlines() if "repro scripts green" in line]
    assert len(findings) == 1
    assert "corpus:" in findings[0] and "2 repro scripts green" in findings[0]


def test_audit_without_matrix_byte_identical_to_pre_s26(tmp_path):
    """Pin (A/B): with no matrix present, run_audit is byte-identical.

    GOLDEN_PRE_S26_BODY is the exact record body captured from the pre-s26
    audit (commit 03cae74) over this fixture via scratch/capture_golden.py.
    Two no-matrix roots must both match it: no evidence dir at all, and
    evidence present holding neither a matrix nor anything parseable. Any
    corpus line or body drift is red; this pin is green pre-merge by
    construction and must stay green after w1's patch.
    """
    root = _audit_base(tmp_path)
    text = audit.run_audit(root).read_text(encoding="utf-8")
    assert text.splitlines()[4:-1] == GOLDEN_PRE_S26_BODY
    assert "corpus" not in text
    empty = _audit_base(tmp_path / "second")  # fresh root: the helper refuses reuse
    (empty / "akar" / "evidence" / "s9").mkdir(parents=True)
    (empty / "akar" / "evidence" / "notes.md").write_text("not a matrix\n")
    text2 = audit.run_audit(empty).read_text(encoding="utf-8")
    assert text2.splitlines()[4:-1] == GOLDEN_PRE_S26_BODY
    assert "corpus" not in text2


def test_audit_malformed_matrix_rows_skipped_with_one_debug_each(tmp_path, caplog):
    """Pin: malformed rows never crash the audit; one DEBUG log each.

    Malformed = a non-structural `|` row (header and separator are
    structure) that carries no ingestable (script, verdict): fewer than 4
    cells, an empty script cell, or a second cell that is no matrix verdict
    token. The valid FAIL row in the same matrix still arms the candidate;
    each malformed row logs exactly one DEBUG record from the rumpun.audit
    logger.

    Red today: no ingestion happens at all (no DEBUG records, no
    candidate).
    """
    root = _audit_base(tmp_path)
    _write_matrix(
        root,
        "s10",
        [
            ("s9/good.py", "FAIL", "assert boom (line 7)", "REGRESSION candidate"),
            ("s9/short.py", "REGRESSION"),  # fewer than 4 cells
            ("", "FAIL", "--", "no script cell"),  # empty script cell
            ("s9/junk.py", "MAYBE", "--", "not a verdict token"),  # no verdict
        ],
        mtime=2_000_000,
    )
    with caplog.at_level(logging.DEBUG, logger="rumpun.audit"):
        text = audit.run_audit(root).read_text(encoding="utf-8")
    candidates = [line for line in text.splitlines() if line.startswith("candidate:")]
    assert len(candidates) == 1
    assert "s9/good.py" in candidates[0] and "assert boom (line 7)" in candidates[0]
    debugs = [
        rec
        for rec in caplog.records
        if rec.levelno == logging.DEBUG and rec.name == "rumpun.audit"
    ]
    assert len(debugs) == 3


# ---------------------------------------------------------------------------
# s27 w2 spec-first pins: tools/render_dashboard.py (dashboard batch renderer)
#
# The tool does not exist yet; these pins are red against pre-s27 code by
# design. w1 owns the tool; the contract these pins ratify:
#
#   CLI:      python tools/render_dashboard.py <project_root>
#             argv[1] is the PROJECT root -- the directory holding .rumpun/.
#   State:    a season is stateful iff rumpun.engine.state_path exists for
#             it (rimba/<sid>/_season/state.json); the tool imports
#             state_path instead of re-deriving the layout by hand.
#   Renders:  one rimba/<sid>/report.html per stateful season, the campaign
#             index rimba/index.html, and the discoveries index
#             rimba/discoveries/index.html -- via report.render_report /
#             render_index / render_discoveries; the tool adds discovery,
#             the batch loop, and skip handling only.
#   Skips:    a declared season without state renders nothing and logs
#             exactly one skip-reason line naming its sid.
#   Failure:  a root with no .rumpun tree logs the reason to stderr and
#             exits nonzero.
#   Bytes:    two consecutive runs over unchanged campaign bytes produce
#             byte-identical outputs; the tool never mutates campaign state.
#
# Pins run the tool through its __main__ entry as a subprocess with the
# repo .venv python. No wall-clock assertions; the timeout is a hang guard.
# ---------------------------------------------------------------------------


def _pin_repo_root():
    """Repo root from this file's location, workspace and merged alike.

    parents[1] is wrong from the season workspace (.rumpun/rimba/s27/w2
    /tests/); the walk-up requires pyproject.toml, src/rumpun/report.py,
    and .venv/bin/python together so archived src/ copies in scratch trees
    never match.
    """
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / ".venv" / "bin" / "python").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _dashboard_tool_path():
    return _pin_repo_root() / "tools" / "render_dashboard.py"


def _dashboard_python():
    venv_python = _pin_repo_root() / ".venv" / "bin" / "python"
    if venv_python.is_file():
        return str(venv_python)
    import sys

    return sys.executable


def _run_dashboard_tool(root):
    """Run the tool's __main__ entry against a project root."""
    import subprocess

    return subprocess.run(
        [_dashboard_python(), str(_dashboard_tool_path()), str(root)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        cwd=str(root),
    )


def _build_dashboard_fixture(root):
    """Campaign fixture: musim declares s1, s2, s3.

    rimba holds state for s1 (WIN) and s2 (LOSS); s3 is declared with a
    bare rimba dir and no state. Returns the project root.
    """
    import json

    rumpun_root = root / ".rumpun"
    (rumpun_root / "musim").mkdir(parents=True)
    for sid, verdict in (("s1", "WIN"), ("s2", "LOSS"), ("s3", None)):
        (rumpun_root / "musim" / f"{sid}.yaml").write_text(
            f"goal: fixture goal for {sid}\n", encoding="utf-8"
        )
        season = rumpun_root / "rimba" / sid
        season.mkdir(parents=True)
        if sid == "s3":
            continue
        (season / "verdicts.jsonl").write_text(
            json.dumps({"season": sid, "verdict": verdict}) + "\n", encoding="utf-8"
        )
        state_dir = season / "_season"
        state_dir.mkdir()
        (state_dir / "state.json").write_text(
            json.dumps(
                {
                    "id": sid,
                    "status": "completed",
                    "started_at": 1.0,
                    "ended_at": 2.0,
                }
            ),
            encoding="utf-8",
        )
    return root


def _rimba_snapshot(root):
    """relpath -> sha256 for every file under .rumpun/rimba (or {})."""
    import hashlib

    rimba = root / ".rumpun" / "rimba"
    out = {}
    if not rimba.is_dir():
        return out
    for path in sorted(rimba.rglob("*")):
        if path.is_file():
            rel = path.relative_to(rimba)
            out[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def test_render_dashboard_renders_stateful_skips_stateless(tmp_path):
    """Pin 1: one run renders exactly the stateful seasons plus both indexes.

    Exactly two season reports (s1, s2), the campaign index, and the
    discoveries index exist after one run; the stateless season s3 renders
    nothing and logs exactly one skip-reason line naming its sid.
    """
    root = _build_dashboard_fixture(tmp_path)
    proc = _run_dashboard_tool(root)
    assert proc.returncode == 0, proc.stderr
    rimba = root / ".rumpun" / "rimba"
    reports = {p.parent.name for p in rimba.glob("s*/report.html") if p.is_file()}
    assert reports == {"s1", "s2"}
    assert (rimba / "index.html").is_file()
    assert (rimba / "discoveries" / "index.html").is_file()
    skip_lines = [
        line
        for line in proc.stderr.splitlines()
        if "s3" in line and "skip" in line.lower()
    ]
    assert len(skip_lines) == 1, proc.stderr


def test_render_dashboard_deterministic_across_runs(tmp_path):
    """Pin 2: two consecutive runs over unchanged bytes are byte-identical.

    The renderers' campaign-strip links depend on which sibling report.html
    files exist at render time (measured: s27 w2 probe, scratch
    probe-fixture.txt, Q3 leak on s1/report.html). A compliant tool
    neutralizes that history -- pre-cleaning its own outputs before the
    render pass, or an order-independent render. The snapshot also covers
    _season/state.json and verdicts.jsonl: the tool never mutates campaign
    bytes.
    """
    root = _build_dashboard_fixture(tmp_path)
    before = _rimba_snapshot(root)
    proc1 = _run_dashboard_tool(root)
    assert proc1.returncode == 0, proc1.stderr
    snap_a = _rimba_snapshot(root)
    proc2 = _run_dashboard_tool(root)
    assert proc2.returncode == 0, proc2.stderr
    snap_b = _rimba_snapshot(root)
    rendered = {
        rel
        for rel in snap_a
        if rel.endswith("report.html") or rel in ("index.html", "discoveries/index.html")
    }
    assert len(rendered) >= 4, sorted(snap_a)
    assert set(snap_a) >= set(before)
    assert snap_a == snap_b, sorted(
        rel for rel in set(snap_a) | set(snap_b) if snap_a.get(rel) != snap_b.get(rel)
    )


def test_render_dashboard_imports_engine_state_path():
    """Pin 3: the stateful/stateless rule comes from the engine.

    The tool imports rumpun.engine.state_path and uses it for the state
    decision instead of re-deriving rimba/<sid>/_season/state.json by
    hand. Source-level pin per the season spec.
    """
    import importlib.util
    import inspect

    tool = _dashboard_tool_path()
    assert tool.is_file(), f"missing tool: {tool}"
    spec = importlib.util.spec_from_file_location("render_dashboard_s27_pin", tool)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = inspect.getsource(module)
    assert "state_path" in source


def test_render_dashboard_missing_rumpun_exits_nonzero(tmp_path):
    """Pin 4: a root with no .rumpun tree is total failure.

    The tool logs the reason to stderr (naming .rumpun) and exits nonzero;
    it must not exit silently or render anything.
    """
    root = tmp_path / "empty"
    root.mkdir()
    proc = _run_dashboard_tool(root)
    assert proc.returncode != 0
    assert ".rumpun" in proc.stderr, proc.stderr


# --- discovery link mapping (s29 w2, L1 closure) --------------------------------

"""Spec-first pins for the discoveries link mapping (s29 w2).

Sources: akar codex-review-2026-09-14 (L1) plus s28-harvest (L1 confirmed
open). Contract under test: every discovery record renders a page its list
link resolves to (the href path exists after render and carries the record
body), ids sharing one sanitized slug render two distinct pages, and an all
lowercase-hyphen ledger (the current ledger) renders byte-identical list
plus pages to the pre-s29 render.

Standalone pins file: tests/test_rumpun.py stays byte-identical
(additions-only constraint). To integrate by appending into
tests/test_rumpun.py instead, drop this import block; the suite already
imports re, Path, and report. GOLDEN_DISCOVERIES is generated from the
pre-s29 code by scratch/capture_golden.py between the sentinels; capture
provenance (git rev, report.py sha256, determinism double-render) lives in
scratch/evidence/golden/capture.log.

Red/green map against pre-s29 code: pins 1-3 red (the list links the raw
id while pages land on the sanitized slug), pin 4 red (a-b and a.b both
write a-b.html and the second overwrites the first), pin 5 green on both
sides (it fails only if the fix drifts current-ledger bytes).
"""



# Clock-free fixed ledger fixture: akar files are written directly because
# akar.append_record stamps date.today(), and a clock read would poison
# pin 5's byte compare. Ids echo the real ledger's lowercase-hyphen shape.
AB_RECORDS: tuple[tuple[str, str, str], ...] = (
    ("audit-1", "reflection audit", "5 dead phases found"),
    ("glm-toolless-spawn", "tool-less spawns", "7 of 24 boot without tools"),
)


def _discovery_root(base: Path, records=AB_RECORDS) -> Path:
    """One .rumpun root whose akar holds fixed-date records; returns root."""
    root = base / "proj" / ".rumpun"
    (root / "akar").mkdir(parents=True)
    for rid, title, body in records:
        (root / "akar" / f"{rid}.md").write_text(
            f"id: {rid}\ntitle: {title}\ndate: 2026-09-15\n\n{body}\n",
            encoding="utf-8",
        )
    return root


def _list_links(out: Path) -> dict[str, str]:
    """The rendered list page's title -> href map."""
    found = re.findall(
        r'<a href="([^"]+)">([^<]+)</a>', out.read_text(encoding="utf-8")
    )
    return {title: href for href, title in found}


def _resolve(out: Path, title: str) -> Path:
    """Resolve the list's link for `title` to a path next to the list page.

    Asserts the entry exists; whether the target file exists stays with the
    caller so a pin failure names the missing page, not the parser.
    """
    links = _list_links(out)
    assert title in links, f"discoveries list lacks an entry for {title!r}: {links}"
    return out.parent / links[title]


def test_discovery_uppercase_id_link_resolves(tmp_path):
    """L1 pin 1: record "Audit-1" renders a page its list link resolves to.

    Red today: the list links the raw id (Audit-1.html) while the page is
    written to the sanitized slug audit-1.html; on a case-sensitive
    filesystem the link resolves to nothing.
    """
    root = _discovery_root(
        tmp_path, (("Audit-1", "uppercase id", "uppercase body line"),)
    )
    out = report.render_discoveries(root)
    page = _resolve(out, "uppercase id")
    assert page.is_file(), f"link href {page.name!r} resolves to no page file"
    assert "uppercase body line" in page.read_text(encoding="utf-8")


def test_discovery_underscore_id_link_resolves(tmp_path):
    """L1 pin 2: record "my_id" renders a page its list link resolves to.

    Red today: the list links my_id.html while the page is written to the
    sanitized slug my-id.html; the link resolves to nothing.
    """
    root = _discovery_root(tmp_path, (("my_id", "underscore id", "underscore body line"),))
    out = report.render_discoveries(root)
    page = _resolve(out, "underscore id")
    assert page.is_file(), f"link href {page.name!r} resolves to no page file"
    assert "underscore body line" in page.read_text(encoding="utf-8")


def test_discovery_dot_id_link_resolves(tmp_path):
    """L1 pin 3: record "a.b" renders a page its list link resolves to.

    Red today: the list links a.b.html while the page is written to the
    sanitized slug a-b.html; the link resolves to nothing.
    """
    root = _discovery_root(tmp_path, (("a.b", "dot id", "dot body line"),))
    out = report.render_discoveries(root)
    page = _resolve(out, "dot id")
    assert page.is_file(), f"link href {page.name!r} resolves to no page file"
    assert "dot body line" in page.read_text(encoding="utf-8")


def test_discovery_slug_collision_two_distinct_pages(tmp_path):
    """L1 pin 4: "a-b" and "a.b" render two distinct pages, no overwrite.

    Red today: both ids sanitize to the same slug, so one page file is
    written twice (the second render overwrites the first) and the list
    then links a.b.html, which was never written at all.
    """
    root = _discovery_root(
        tmp_path,
        (
            ("a-b", "collision hyphen", "hyphen body line"),
            ("a.b", "collision dot", "dot body line"),
        ),
    )
    out = report.render_discoveries(root)
    hyphen = _resolve(out, "collision hyphen")
    dot = _resolve(out, "collision dot")
    assert hyphen != dot, f"both links resolve to one page file: {hyphen.name}"
    assert hyphen.is_file(), f"link href {hyphen.name!r} resolves to no page file"
    assert dot.is_file(), f"link href {dot.name!r} resolves to no page file"
    hyphen_text = hyphen.read_text(encoding="utf-8")
    dot_text = dot.read_text(encoding="utf-8")
    assert "hyphen body line" in hyphen_text
    assert "dot body line" in dot_text
    assert "dot body line" not in hyphen_text, "dot page overwrote the hyphen page"
    assert "hyphen body line" not in dot_text, "hyphen page overwrote the dot page"


def test_discoveries_bytes_unchanged_from_pre_s29(tmp_path):
    """L1 pin 5 (A/B regression): the current ledger's id shape (all
    lowercase-hyphen) renders byte-identical list and pages to the
    pre-s29 render.

    Green before and after the fix; red the moment any byte drifts for
    the current ledger's shape. Golden bytes were captured from the
    pre-s29 code by scratch/capture_golden.py; capture provenance (git
    rev, report.py sha256, determinism double-render) lives in
    scratch/evidence/golden/capture.log.
    """
    root = _discovery_root(tmp_path)
    out = report.render_discoveries(root)
    written = sorted(p.name for p in out.parent.glob("*.html"))
    assert written == sorted(GOLDEN_DISCOVERIES), f"page set drifted: {written}"
    for name, golden in GOLDEN_DISCOVERIES.items():
        assert (out.parent / name).read_bytes() == golden, f"bytes drifted: {name}"


# --- BEGIN GOLDEN_DISCOVERIES (generated; do not hand-edit) ---
GOLDEN_DISCOVERIES: dict[str, bytes] = {
    "audit-1.html": (
        b'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8'
        b'">\n<meta name="viewport" content="width=device-width, initia'
        b'l-scale=1">\n<title>rumpun discovery audit-1</title>\n<style>b'
        b'ody{background:#020617;color:#F8FAFC;font-family:Inter,ui-sa'
        b'ns-serif,system-ui,sans-serif;margin:0;padding:1.5rem;max-wi'
        b'dth:64rem;margin-inline:auto}\na{color:#38BDF8;text-decoratio'
        b'n:none}a:focus-visible{outline:2px solid #F8FAFC}\nh1{font-si'
        b'ze:1.25rem;margin:0 0 .25rem}h2{font-size:.95rem;color:#94A3'
        b'B8;margin:1.5rem 0 .5rem;text-transform:uppercase;letter-spa'
        b'cing:.08em}}\n.card{background:#0E1223;border:1px solid #3341'
        b'55;border-radius:8px;padding:1rem;margin-top:.75rem}\ntable{b'
        b'order-collapse:collapse;width:100%;margin-top:.5rem}\nth,td{b'
        b'order:1px solid #334155;padding:.35rem .6rem;text-align:left'
        b';font-family:ui-monospace,monospace;font-size:.85rem}\nth{bac'
        b'kground:#020617;color:#94A3B8;font-weight:600}\n.prov{font-si'
        b'ze:.75em;color:#94A3B8;font-weight:normal}\n.policy,.legend-n'
        b'ote{color:#94A3B8;font-size:.85rem}\n.legend ul{margin:.3rem '
        b'0;padding-left:1.2rem}\n.footer{color:#94A3B8;font-size:.8rem'
        b';margin-top:2rem}\n.strip{display:flex;flex-wrap:wrap;gap:.5r'
        b'em}\n.strip a{display:block;min-width:6.2rem}\n.cell{border:1p'
        b'x solid #334155;border-radius:8px;padding:.5rem .6rem;backgr'
        b'ound:#0E1223}\n.cell .sid{font-family:ui-monospace,monospace;'
        b'font-weight:600}\n.cell .ver{font-size:.75rem}\n.change dt{mar'
        b'gin-top:.5rem}\n.change dd{margin:0 0 .25rem;font-family:ui-m'
        b'onospace,monospace;font-size:.85rem}\n.bar{fill:#38BDF8}.barl'
        b'oss{fill:#EF4444}.barwin{fill:#22C55E}\n.stat{display:flex;ga'
        b'p:1rem;flex-wrap:wrap;margin-top:.5rem}\n.stat .card{margin:0'
        b';flex:1;min-width:9rem}\n.stat .num{font-size:1.6rem;font-fam'
        b'ily:ui-monospace,monospace}\n.stat .lbl{color:#94A3B8;font-si'
        b'ze:.8rem}\n.one{font-size:.95rem;margin:.4rem 0 0}\n.plain{fon'
        b't-size:1rem;margin:.25rem 0}\n.idle{color:#94A3B8}</style>\n</'
        b'head>\n<body>\n<h1>reflection audit</h1>\n<p class="plain"><spa'
        b'n class="prov">audit-1 &middot; 2026-09-15 [A]</span> &middo'
        b't; <a href="index.html">all discoveries</a></p>\n<pre>id: aud'
        b'it-1\ntitle: reflection audit\ndate: 2026-09-15\n\n5 dead phases'
        b' found\n</pre>\n<p class="policy">State policy [D]: exit file '
        b'0 -&gt; exited; non-zero -&gt; failed; no exit file + live p'
        b'id -&gt; running (stalled after stall_minutes); no exit file'
        b' + dead pid -&gt; crashed; engine kill -&gt; terminated.</p>'
        b'\n</body>\n</html>\n'
    ),
    "glm-toolless-spawn.html": (
        b'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8'
        b'">\n<meta name="viewport" content="width=device-width, initia'
        b'l-scale=1">\n<title>rumpun discovery glm-toolless-spawn</titl'
        b'e>\n<style>body{background:#020617;color:#F8FAFC;font-family:'
        b'Inter,ui-sans-serif,system-ui,sans-serif;margin:0;padding:1.'
        b'5rem;max-width:64rem;margin-inline:auto}\na{color:#38BDF8;tex'
        b't-decoration:none}a:focus-visible{outline:2px solid #F8FAFC}'
        b'\nh1{font-size:1.25rem;margin:0 0 .25rem}h2{font-size:.95rem;'
        b'color:#94A3B8;margin:1.5rem 0 .5rem;text-transform:uppercase'
        b';letter-spacing:.08em}}\n.card{background:#0E1223;border:1px '
        b'solid #334155;border-radius:8px;padding:1rem;margin-top:.75r'
        b'em}\ntable{border-collapse:collapse;width:100%;margin-top:.5r'
        b'em}\nth,td{border:1px solid #334155;padding:.35rem .6rem;text'
        b'-align:left;font-family:ui-monospace,monospace;font-size:.85'
        b'rem}\nth{background:#020617;color:#94A3B8;font-weight:600}\n.p'
        b'rov{font-size:.75em;color:#94A3B8;font-weight:normal}\n.polic'
        b'y,.legend-note{color:#94A3B8;font-size:.85rem}\n.legend ul{ma'
        b'rgin:.3rem 0;padding-left:1.2rem}\n.footer{color:#94A3B8;font'
        b'-size:.8rem;margin-top:2rem}\n.strip{display:flex;flex-wrap:w'
        b'rap;gap:.5rem}\n.strip a{display:block;min-width:6.2rem}\n.cel'
        b'l{border:1px solid #334155;border-radius:8px;padding:.5rem .'
        b'6rem;background:#0E1223}\n.cell .sid{font-family:ui-monospace'
        b',monospace;font-weight:600}\n.cell .ver{font-size:.75rem}\n.ch'
        b'ange dt{margin-top:.5rem}\n.change dd{margin:0 0 .25rem;font-'
        b'family:ui-monospace,monospace;font-size:.85rem}\n.bar{fill:#3'
        b'8BDF8}.barloss{fill:#EF4444}.barwin{fill:#22C55E}\n.stat{disp'
        b'lay:flex;gap:1rem;flex-wrap:wrap;margin-top:.5rem}\n.stat .ca'
        b'rd{margin:0;flex:1;min-width:9rem}\n.stat .num{font-size:1.6r'
        b'em;font-family:ui-monospace,monospace}\n.stat .lbl{color:#94A'
        b'3B8;font-size:.8rem}\n.one{font-size:.95rem;margin:.4rem 0 0}'
        b'\n.plain{font-size:1rem;margin:.25rem 0}\n.idle{color:#94A3B8}'
        b'</style>\n</head>\n<body>\n<h1>tool-less spawns</h1>\n<p class="'
        b'plain"><span class="prov">glm-toolless-spawn &middot; 2026-0'
        b'9-15 [A]</span> &middot; <a href="index.html">all discoverie'
        b's</a></p>\n<pre>id: glm-toolless-spawn\ntitle: tool-less spawn'
        b's\ndate: 2026-09-15\n\n7 of 24 boot without tools\n</pre>\n<p cla'
        b'ss="policy">State policy [D]: exit file 0 -&gt; exited; non-'
        b'zero -&gt; failed; no exit file + live pid -&gt; running (st'
        b'alled after stall_minutes); no exit file + dead pid -&gt; cr'
        b'ashed; engine kill -&gt; terminated.</p>\n</body>\n</html>\n'
    ),
    "index.html": (
        b'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8'
        b'">\n<meta name="viewport" content="width=device-width, initia'
        b'l-scale=1">\n<title>rumpun discoveries</title>\n<style>body{ba'
        b'ckground:#020617;color:#F8FAFC;font-family:Inter,ui-sans-ser'
        b'if,system-ui,sans-serif;margin:0;padding:1.5rem;max-width:64'
        b'rem;margin-inline:auto}\na{color:#38BDF8;text-decoration:none'
        b'}a:focus-visible{outline:2px solid #F8FAFC}\nh1{font-size:1.2'
        b'5rem;margin:0 0 .25rem}h2{font-size:.95rem;color:#94A3B8;mar'
        b'gin:1.5rem 0 .5rem;text-transform:uppercase;letter-spacing:.'
        b'08em}}\n.card{background:#0E1223;border:1px solid #334155;bor'
        b'der-radius:8px;padding:1rem;margin-top:.75rem}\ntable{border-'
        b'collapse:collapse;width:100%;margin-top:.5rem}\nth,td{border:'
        b'1px solid #334155;padding:.35rem .6rem;text-align:left;font-'
        b'family:ui-monospace,monospace;font-size:.85rem}\nth{backgroun'
        b'd:#020617;color:#94A3B8;font-weight:600}\n.prov{font-size:.75'
        b'em;color:#94A3B8;font-weight:normal}\n.policy,.legend-note{co'
        b'lor:#94A3B8;font-size:.85rem}\n.legend ul{margin:.3rem 0;padd'
        b'ing-left:1.2rem}\n.footer{color:#94A3B8;font-size:.8rem;margi'
        b'n-top:2rem}\n.strip{display:flex;flex-wrap:wrap;gap:.5rem}\n.s'
        b'trip a{display:block;min-width:6.2rem}\n.cell{border:1px soli'
        b'd #334155;border-radius:8px;padding:.5rem .6rem;background:#'
        b'0E1223}\n.cell .sid{font-family:ui-monospace,monospace;font-w'
        b'eight:600}\n.cell .ver{font-size:.75rem}\n.change dt{margin-to'
        b'p:.5rem}\n.change dd{margin:0 0 .25rem;font-family:ui-monospa'
        b'ce,monospace;font-size:.85rem}\n.bar{fill:#38BDF8}.barloss{fi'
        b'll:#EF4444}.barwin{fill:#22C55E}\n.stat{display:flex;gap:1rem'
        b';flex-wrap:wrap;margin-top:.5rem}\n.stat .card{margin:0;flex:'
        b'1;min-width:9rem}\n.stat .num{font-size:1.6rem;font-family:ui'
        b'-monospace,monospace}\n.stat .lbl{color:#94A3B8;font-size:.8r'
        b'em}\n.one{font-size:.95rem;margin:.4rem 0 0}\n.plain{font-size'
        b':1rem;margin:.25rem 0}\n.idle{color:#94A3B8}</style>\n</head>\n'
        b'<body>\n<h1>Discoveries</h1>\n<p class="plain">What the campai'
        b'gn learned about itself and its tools <span class="prov">[A]'
        b'</span> &middot; <a href="../index.html">all progress</a></p'
        b'>\n<ul><li><a href="glm-toolless-spawn.html">tool-less spawns'
        b'</a> <span class="prov">glm-toolless-spawn &middot; 2026-09-'
        b'15</span></li><li><a href="audit-1.html">reflection audit</a'
        b'> <span class="prov">audit-1 &middot; 2026-09-15</span></li>'
        b'</ul>\n<p class="policy">State policy [D]: exit file 0 -&gt; '
        b'exited; non-zero -&gt; failed; no exit file + live pid -&gt;'
        b' running (stalled after stall_minutes); no exit file + dead '
        b'pid -&gt; crashed; engine kill -&gt; terminated.</p>\n</body>'
        b'\n</html>\n'
    ),
}
# --- END GOLDEN_DISCOVERIES ---


# --- s30 w2 pins (harness-integrated salvage) ---

"""s30 w2 spec-first pins: `audit --corpus` runs the fresh-matrix gate.

Spec-first pins, RED against the pre-s30 code (commit 9376dfb, akar
audit-18): today the audit verb accepts no --corpus flag, never invokes
the replay runner, and only ingests the newest COMMITTED evidence matrix.
These pins ratify the s30 contract (musim/s30.yaml, w1 deliverable):

1. `audit --corpus` runs the corpus runner as an isolated subprocess
   (stub runner file at <repo>/tools/replay_corpus.py) BEFORE ingesting,
   and the FRESH matrix's REGRESSION row arms the corpus candidate (the
   stale all-green committed matrix never does).
2. A runner failing with exit 1 raises AuditError naming the runner and
   the exit code; no record is appended, so no stale matrix is ingested.
3. A runner timeout raises AuditError (bounded: timeout_s=1 on a stub
   sleeping 30s; the pin fails on any wait beyond 15s wall).
4. Without --corpus, the audit record body is byte-identical to the
   pre-s30 output (GOLDEN_BODY, captured from unpatched code by
   scratch/capture_golden.py, stamped sha256 85f44e1c...; decoy uncommitted
   matrix at the repo root stays un-read).
5. Regression: the 138-test suite stays green (evidence:
   scratch/evidence/suite-run.txt; pins file is additions-only and the
   repo tests/ file stays byte-identical).

Standalone on purpose: merge by appending to tests/test_rumpun.py and
dropping the duplicated fixture helpers (suite helpers are verbatim
copies of the s11-s26 audit fixtures).
"""





S30_RUMPUN_YAML = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "cat {prompt} | true"
"""

S30_AUDIT_SEASON = """\
id: {sid}
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
    eval_window: "{sid}"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
    - phase: evaluate
      primitive: evaluate
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: verdicts.jsonl
benih:
  - name: w1
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [all_exited]
"""


def _s30_write_proj(base: Path) -> Path:
    """Audit fixture: .rumpun project root + repo-root analog with tools/."""
    root = base / "proj" / ".rumpun"
    (root / "musim").mkdir(parents=True)
    (root / "akar").mkdir()
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(S30_RUMPUN_YAML, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    for sid in ("s1", "s2"):
        (root / "musim" / f"{sid}.yaml").write_text(
            S30_AUDIT_SEASON.format(sid=sid), encoding="utf-8"
        )
    season = root / "rimba" / "s1"
    season.mkdir(parents=True)
    (season / "results.jsonl").write_text('{"n": 1}\n', encoding="utf-8")
    (season / "verdicts.jsonl").write_text('{"v": "WIN"}\n', encoding="utf-8")
    state = season / "_season"
    state.mkdir()
    (state / "state.json").write_text(
        json.dumps({"id": "s1", "status": "completed", "started_at": 1.0, "ended_at": 2.0}),
        encoding="utf-8",
    )
    (root / "rimba" / "s2").mkdir(parents=True)
    return root


def _write_stale_matrix(root: Path) -> Path:
    """All-green committed matrix at akar/evidence/s9 (the stale s26 input)."""
    directory = root / "akar" / "evidence" / "s9"
    directory.mkdir(parents=True, exist_ok=True)
    lines = [
        "# stale committed matrix (captured before s30)",
        "",
        "| script | verdict | first failing line | note |",
        "|---|---|---|---|",
        "| stale/green-a.py | PASS | -- | exit 0; all-pass signature matched |",
        "| stale/green-b.py | PASS | -- | exit 0; all-pass signature matched |",
    ]
    path = directory / "replay-matrix.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_stub_runner(repo: Path, source: str) -> Path:
    """The stub runner file at <repo analog>/tools/replay_corpus.py.

    The runner path resolves relative to the repo root (the .rumpun
    project root's parent), so the fixture plants the stub exactly where
    the implementation must find it; its name is the real runner's name,
    so error-message pins hold against either spelling.
    """
    tools = repo / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    path = tools / "replay_corpus.py"
    path.write_text(source, encoding="utf-8")
    return path


STUB_OK = '''#!/usr/bin/env python3
"""Stub corpus runner: writes a fresh matrix with one FAIL/REGRESSION row; exit 0."""
import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--evidence", type=Path, default=None)
    parser.add_argument(
        "--out-dir", type=Path, default=Path(__file__).resolve().parent.parent
    )
    parser.add_argument("--only", default=None)
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# stub corpus matrix (fresh run)",
        "",
        "| script | verdict | first failing line | note |",
        "|---|---|---|---|",
        "| freshreg/probe.py | FAIL | -- | REGRESSION candidate; exit 1; see logs |",
    ]
    (out_dir / "replay-matrix.md").write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    marker = Path(__file__).resolve().parent / ".stub-ran"
    marker.write_text("stub ran as a subprocess\\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

STUB_FAIL = '''#!/usr/bin/env python3
"""Stub corpus runner: proves invocation with a marker, then exits 1."""
import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--evidence", type=Path, default=None)
    parser.add_argument(
        "--out-dir", type=Path, default=Path(__file__).resolve().parent.parent
    )
    parser.add_argument("--only", default=None)
    args = parser.parse_args()
    marker = Path(__file__).resolve().parent / ".stub-ran"
    marker.write_text("stub ran then failed\\n", encoding="utf-8")
    return 1


if __name__ == "__main__":
    sys.exit(main())
'''

STUB_SLEEP = '''#!/usr/bin/env python3
"""Stub corpus runner: sleeps 30s (killed by the bounded timeout)."""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--evidence", type=Path, default=None)
    parser.add_argument(
        "--out-dir", type=Path, default=Path(__file__).resolve().parent.parent
    )
    parser.add_argument("--only", default=None)
    args = parser.parse_args()
    time.sleep(30)
    return 0


if __name__ == "__main__":
    sys.write... write marker
    sys.exit(main())
'''

GOLDEN_BODY = [
    "scope: last 2 musim seasons (s1,s2); engine seasons with rimba/ (2): s1,s2",
    "declared phases from latest season s2: execute->results.jsonl, "
    "evaluate->verdicts.jsonl",
    "F1 phase liveness: phase execute (writes results.jsonl) wrote its "
    "artifact in 1 of 2 engine seasons (s1,s2)",
    "F1 phase liveness: phase evaluate (writes verdicts.jsonl) wrote its "
    "artifact in 1 of 2 engine seasons (s1,s2)",
    "F2 stall recurrence: stopped_stall in 0 of 1 seasons with state.json "
    "(none); recurrence no (threshold 2)",
    "F3 verdict histogram over verdicts.jsonl of s1 (none in: s2): WIN 0, "
    "LOSS 0, INVALID 0",
    "F4 route outcomes: no finalized agent snapshots in audited engine "
    "seasons (s1,s2)",
    "F5 band calibration: no LOSS season shipped integrated modules (s1)",
    "F6 budget compliance: campaign_cost_cap unset since campaign start (P9) "
    "— operator sets the number; the tool only flags",
    "corpus: 2 repro scripts green on main (no candidates)",
    "candidates: none — no trigger met; nothing proposed without evidence",
]


def _audit_flags() -> list[str]:
    return ["audit", "--corpus"]


def _parse_audit(args: list[str]):
    """The audit subcommand namespace (SystemExit 2 while --corpus is missing)."""
    return cli_mod.build_parser().parse_args(args)


def test_audit_corpus_flag_runs_runner_and_ingests_fresh_matrix(tmp_path, capsys, monkeypatch):
    """Pin 1: --corpus runs the runner (isolated subprocess) before ingesting.

    The stub runner writes a FRESH matrix holding one FAIL row whose note
    names REGRESSION, plus a marker file only a real subprocess creates.
    The committed stale matrix in the same fixture is all-green, so a
    record citing freshreg/probe.py proves the fresh matrix was ingested
    (content that can only exist after the runner ran), and the marker
    proves the runner executed as its own process.
    """
    root = _s30_write_proj(tmp_path)
    _write_stale_matrix(root)
    repo = root.parent
    _write_stub_runner(repo, STUB_OK)
    monkeypatch.chdir(repo)
    args = _parse_audit(["audit", "--corpus"])
    rc = args.func(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "candidate: corpus regression" in out
    assert "freshreg/probe.py" in out
    marker = repo / "tools" / ".stub-ran"
    assert marker.is_file(), "the stub runner never executed as a subprocess"
    records = sorted((root / "akar").glob("*_audit-*.md"))
    assert len(records) == 1
    text = records[0].read_text(encoding="utf-8")
    assert "candidate: corpus regression: freshreg/probe.py" in text
    assert "stale/green-a.py" not in text  # the stale matrix was never the input


def test_audit_corpus_runner_exit_1_honest_error_no_ingestion(tmp_path, monkeypatch):
    """Pin 2: runner exit 1 -> AuditError naming runner + code, no ingestion.

    The stub writes its marker and exits 1. The audit must refuse the run:
    AuditError carrying the runner name and the exit code, and the akar
    directory must gain no record (an all-green stale matrix sits in
    evidence; silently ingesting it here would be the lie this pin bans).
    """
    root = _s30_write_proj(tmp_path)
    _write_stale_matrix(root)
    repo = root.parent
    _write_stub_runner(repo, STUB_FAIL)
    monkeypatch.chdir(repo)
    args = _parse_audit(["audit", "--corpus"])
    before = sorted(p.name for p in (root / "akar").iterdir())
    with pytest.raises(audit_mod.AuditError) as excinfo:
        args.func(args)
    msg = str(excinfo.value)
    assert "replay_corpus.py" in msg, f"runner not named: {msg}"
    assert "exit" in msg.lower()
    assert re.search(r"(?<!\d)1(?!\d)", msg), f"exit code not named: {msg}"
    after = sorted(p.name for p in (root / "akar").iterdir())
    assert after == before, "the failed run mutated akar/"
    assert not list((root / "akar").glob("*_audit-*.md"))


def test_audit_corpus_runner_timeout_bounded(tmp_path):
    """Pin 3: a runner timeout raises AuditError, bounded in wall time.

    refresh_corpus_matrix is the named w1 seam: (root, runner_path,
    timeout_s). The stub sleeps 30s; timeout_s=1 must kill it and raise
    AuditError naming the runner. The pin fails on any wait beyond 15s
    wall (15x the budget, generous for CI load), and no record may land.
    """
    root = _s30_write_proj(tmp_path)
    repo = root.parent
    stub = _write_stub_runner(repo, STUB_SLEEP)
    refresh = getattr(audit_mod, "refresh_corpus_matrix", None)
    if refresh is None:
        pytest.fail("rumpun.audit has no refresh_corpus_matrix (w1 seam missing)")
    started = time.perf_counter()
    with pytest.raises(audit_mod.AuditError) as excinfo:
        refresh(root, runner_path=stub, timeout_s=1)
    elapsed = time.perf_counter() - started
    assert elapsed < 15.0, f"timeout path waited {elapsed:.1f}s; the budget is 1s"
    assert "replay_corpus.py" in str(excinfo.value)
    assert not list((root / "akar").glob("*_audit-*.md"))


def test_audit_without_corpus_flag_byte_identical(tmp_path):
    """Pin 4 (A/B): without --corpus, the record body is byte-identical.

    GOLDEN_BODY is the exact pre-s30 body captured from unpatched code
    (git 9376dfb, audit.py sha256 972eb574...) by scratch/capture_golden.py
    over this same fixture, with readback and transcription gates. The
    fixture carries the stale all-green evidence matrix (so the default
    s26 stale-ingestion behavior must keep holding) plus an uncommitted
    decoy replay-matrix.md at the repo-root analog (must stay un-read
    without the flag).
    """
    root = _s30_write_proj(tmp_path)
    _write_stale_matrix(root)
    (root.parent / "replay-matrix.md").write_text(
        "uncommitted runner output: decoy that must stay un-read without"
        " --corpus\n",
        encoding="utf-8",
    )
    record = audit_mod.run_audit(root)
    text = record.read_text(encoding="utf-8")
    assert text.splitlines()[4:-1] == GOLDEN_BODY
    assert "decoy" not in text
    assert not [ln for ln in text.splitlines() if ln.startswith("candidate:")]