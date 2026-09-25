# Task: extend tests/test_rumpun.py for the engine state lock + protocol v2 dogfood

Workspace: /mnt/data/work/rumpun/rimba -- corrected workspace:
/mnt/data/work/rumpun/.rumpun/rimba/s5/w2. Write ONLY test_rumpun.py,
notes.md, lane_tool.py into this workspace. Do not touch anything outside it.

Base your test_rumpun.py on the CURRENT repo file
/mnt/data/work/rumpun/tests/test_rumpun.py (read it first; keep all 18
existing tests passing).

Add, at minimum:
1. State lock: after engine._save_state writes a tmp project state, a
   state.lock file exists in the same dir. Then a concurrent-writers test:
   4 threads x 10 calls to _save_state on one state path, each writing
   {"n": k*10+i}; after joining, state.json parses and state.lock exists.
2. _agent_snap terminated-marker tests already exist; do not duplicate them.

Collab lane (dogfood retry, protocol v2 — NON-BLOCKING):
- RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK env vars are exported to you.
- lane_tool.py: argv (kind, text) appends {"from": "w2", "kind": kind,
  "text": text} via
  rumpun.collab.append_event from the env vars; argv ("read", "") prints
  events.
- Protocol v2: post kind=start, then kind=policy stating the lock-test
  contract you coded against, then kind=done. Do NOT wait for w1. If w1's
  policy event appears, note agreement or disagreement in notes.md.

Rules: pytest only; no skips; no mocks; ruff clean, line-length 100,
py3.10+. notes.md: what you added, what you left out.
