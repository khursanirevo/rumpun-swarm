"""Tests for the rumpun core modules: engine internals, akar records, harvest,
evolve draft/apply, lint findings, report rendering, and the collab lane.

Everything runs on tmp_path fixtures: no network, no repo state, no skips.
The collab tests are spec-first: rumpun.collab lands at integration (w1's
lane module) with the ratified contract — prepare_lane creates the lane/lock
pair without truncating, append_event writes one JSON line under flock with
seq = existing line count, read_events replays in file order and raises
LaneError on a corrupt line.
"""

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from rumpun import akar, engine, evolve, harvest, lint, report

# isort: split
from rumpun import collab  # spec-first: module lands at integration

RUMPUN_YAML = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
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


def _write_proj(tmp_path, season_text, season_name="s1.yaml"):
    """Build <tmp>/proj/.rumpun: rumpun.yaml, one season, the dummy prompt."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "musim").mkdir(parents=True)
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(RUMPUN_YAML, encoding="utf-8")
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
