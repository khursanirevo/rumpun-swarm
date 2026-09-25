# Task: add a state lock to src/rumpun/engine.py (full file into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s5/w1. Write ONLY engine.py,
notes.md, lane_tool.py into this workspace. Do not touch anything outside it.

Base your engine.py on the CURRENT repo file
/mnt/data/work/rumpun/src/rumpun/engine.py (read it first; keep the collab
lane env wiring and the terminated-marker logic intact — they are new and
tested).

Defect (season ids are singletons): two processes running
`rumpun season start` for the same season id interleave writes to
.rumpun/rimba/<sid>/_season/state.json. Atomic tmp+replace prevents torn
files but not lost updates: one watcher's state overwrites the other's.

Required fix, nothing else:
- _save_state takes or flocks a lock: hold an exclusive flock on
  <season>/_season/state.lock for the read-modify-write cycle in
  start_season, and for single writes. Simplest correct shape:
  _save_state opens/creates state.lock, flock LOCK_EX, writes tmp, replaces,
  unlocks. Callers stay the same.
- The read-modify-write in start_season stays under one lock acquisition
  where practical; do not restructure beyond that.
- Everything else behaviorally identical; all 18 tests must keep passing.

Collab lane (dogfood retry, protocol v2 — NON-BLOCKING):
- RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK env vars are exported to you.
- lane_tool.py: argv (kind, text) appends {"from": "w1", "kind": kind,
  "text": text} via rumpun.collab.append_event from the env vars; argv
  ("read", "") prints events.
- Protocol v2: post kind=start at the beginning, kind=policy stating your
  exact lock design BEFORE you finish, kind=done at the end. Do NOT wait
  for w2. If w2 posts a claim or question, address it in notes.md; the
  defaults in this prompt are the contract, lane events refine them.

Rules: stdlib only; logging, never print (lane_tool may print). ruff clean,
line-length 100, py3.10+.
