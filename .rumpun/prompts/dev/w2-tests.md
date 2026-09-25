# Task: write tests/test_rumpun.py (pytest suite; collab tests are spec-first)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s3/w2. Write ONLY test_rumpun.py,
notes.md into this workspace. Do not touch anything outside it.

The suite lands at repo tests/test_rumpun.py and runs with: uv run pytest -q.
Import targets exactly:
  from rumpun import akar, engine, evolve, harvest, lint, report
  from rumpun import collab          # spec-first: module lands at integration
Use tmp_path fixtures; no network; no skips; every test runnable as written.

Cover, at minimum:
1. engine._proc_start_ticks(4194303) is None (no /proc entry).
2. engine._stop_rules on a season dict with stop.on [all_exited,
   {stall_minutes: 15}] and one benih budget {minutes: 20} -> (900.0, 1200.0).
3. engine._agent_snap over a tmp workspace dir: write state.json
   {"name": "a", "route": "glm", "cmd": "x", "pid": 1, "proc_start": 987654321,
   "started_at": 0.0} (proc_start mismatch means dead). With exit file "0"
   -> "exited"; "3" -> "failed"; no exit file -> "crashed".
4. akar.append_record in a tmp dir: file <date>_<id>.md contains the id, the
   title, the body and a "sha256:" line; appending the same id again raises
   akar.AkarError.
5. harvest.harvest_season(tmp root, "s1", "WIN", "note") writes an akar record
   containing the verdict text.
6. evolve.draft_next from a minimal parent (fixture below) drafts s2.yaml whose
   primary_change fields are empty; evolve.apply on that draft raises
   evolve.EvolveError.
7. lint.lint on a season yaml with an empty baseline field returns a Finding
   with severity "error".
8. collab (spec-first): prepare_lane then two append_event calls ->
   read_events returns seq 0 then 1 with the right senders; a file with one
   corrupt line makes read_events raise collab.LaneError.
9. report._document on a hand-built status dict {"id": "s1",
   "status": "completed", "started_at": 1.0, "ended_at": 2.0,
   "agents": {"w1": {"name": "w1", "route": "glm", "state": "exited",
   "exit_code": 0, "seconds": 1.0}}}: output contains the season id and all
   three provenance labels [H], [A], [D]; two calls return byte-identical text.

Minimal valid season yaml for fixture 6 (verbatim):
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
Tmp project layout for fixture 6/7:
  <tmp>/proj/.rumpun/rumpun.yaml :
    autonomy:
      stage: manual
      invariants: [goal_immutable, budget_cap, falsify_required]
    routes:
      glm: "cat {prompt} | true"
  <tmp>/proj/.rumpun/musim/s1.yaml : the season above
  <tmp>/proj/.rumpun/prompts/dev/dummy.md : any text

collab API the tests may rely on (identical to the writer's spec):
  prepare_lane(root, sid, group) -> {"file": str, "lock": str}
  append_event(lane, sender, payload) -> dict   # flock LOCK_EX, seq = line count
  read_events(lane) -> list[dict]               # LaneError on corrupt line

Rules: pytest only. logging, never print. ruff clean, line-length 100,
py3.10+. notes.md: how to run the suite and what you deliberately left out.
