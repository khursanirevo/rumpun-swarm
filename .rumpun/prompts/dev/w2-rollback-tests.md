# Task: spec-first tests for evolve rollback (full test file into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s9/w2. Write ONLY
test_rumpun.py, notes.md, lane_tool.py into this workspace. Do not touch
anything outside it.

Base your test_rumpun.py on the CURRENT repo file
/mnt/data/work/rumpun/tests/test_rumpun.py (read it first; keep all 24
existing tests passing).

The function lands at integration (spec; author against exactly this):
  evolve.rollback_season(root: Path, sid: str) -> Path
    - sid must match s<N> (evolve.EvolveError otherwise);
    - musim/<sid>.yaml must exist (EvolveError with a "use reject" hint if
      missing);
    - moves it to root/musim/rejected/<sid>.yaml (dir created, collision ->
      EvolveError);
    - appends akar record id "rollback-<sid>" whose body contains
      "rollback_to_last_good" and "git revert";
    - akar.AkarError wraps into EvolveError; returns the record path.

Add, at minimum:
1. rollback_season on a tmp project season: original yaml gone, musim/
   rejected/<sid>.yaml exists, akar record text contains "rollback-<sid>",
   "rollback_to_last_good", and "git revert".
2. Missing season raises EvolveError.
3. Non-s<N> sid ("x9", "season1") raises EvolveError.
4. Second rollback of the same sid raises EvolveError (file already moved).

Collab lane (protocol v2, NON-BLOCKING — evidence gathering only):
- RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK are exported to you.
- lane_tool.py: argv (kind, text) appends {"from": "w2", "kind": kind,
  "text": text} via rumpun.collab.append_event from the env vars; argv
  ("read", "") prints events. Post kind=start, kind=policy, kind=done.
  Never wait on w1.

Rules: pytest only; no skips; no mocks. ruff clean, line-length 100,
py3.10+. notes.md: what you added, what you left out.
