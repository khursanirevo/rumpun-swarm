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
campaign.budget.campaign_cost_cap (finding only, never a candidate),
candidate priority phase -> route -> calibration under MAX_CANDIDATES = 3,
and musim/ plus rimba/ still byte-identical after run_audit.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from rumpun import akar, engine, evolve, harvest, lint, report

# isort: split
from rumpun import audit, collab  # spec-first: modules land at integration

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
campaign:
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


def test_dual_start_single_spawner(tmp_path):
    """Two concurrent `rumpun season start` processes spawn each agent once.

    Starter 1 holds _season/state.lock across load, the finished check, the
    initial save, and the whole spawn loop. Starter 2 blocks on the flock,
    then reads the fully spawned state and reattaches (both names already in
    `spawned` -> continue) instead of spawning again. Proven by: both exit 0,
    the season reaches exactly one terminal state.json with status
    completed, each benih name appears in the spawned map exactly once, both
    per-agent workspaces hold a state.json, and the "spawned alpha" log line
    appears in exactly one of the two stderr streams.
    """
    root, season = _write_proj(tmp_path, SEASON_DUAL, project_yaml=RUMPUN_YAML_DUAL)
    cmd = [sys.executable, "-m", "rumpun", "season", "start", str(season)]
    # Both Popens go out back-to-back so starter 2 reaches the flock while
    # starter 1 still holds it; its state read then happens under the lock.
    starters = [
        subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(tmp_path),
        )
        for _ in range(2)
    ]
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
    """A real akar <sid>-harvest record — the verdict system of record."""
    return akar.append_record(
        root,
        f"{sid}-harvest",
        f"season {sid} harvest",
        f"season {sid}: completed\n\nverdict: {verdict}\nimplies: fixture",
    )


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
    for sid in ("s1", "s2"):
        # verdicts.jsonl absent in both engine seasons: the evaluate phase
        # is dead and owns the first candidate slot.
        (root / "rimba" / sid / "verdicts.jsonl").unlink()
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
