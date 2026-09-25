# Task: extend tests/test_rumpun.py for the kill-marker fix and lane concurrency

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s4/w2. Write ONLY
test_rumpun.py, notes.md, lane_tool.py into this workspace. Do not touch
anything outside it.

Base your test_rumpun.py on the CURRENT repo file
/mnt/data/work/rumpun/tests/test_rumpun.py (read it first; keep all
existing tests passing).

Add, at minimum:
1. engine._agent_snap: workspace with a "terminated" marker file (and dead
   pid, no exit file) -> state "terminated", exit_code None.
2. Same but with BOTH marker and exit file "0" -> "exited" (exit file wins
   per the ratified policy order).
3. Same marker but exit file "3" -> "failed".
4. collab.append_event under concurrency: 4 threads x 25 appends each ->
   100 event lines, seqs are exactly 0..99 with no gaps or duplicates
   (ThreadPoolExecutor; this proves the flock critical section).

Collab lane (live dogfood — the point of this season):
- RUMPUN_LANE_FILE and RUMPUN_LANE_LOCK are exported to your process.
- Create lane_tool.py: argv (kind, text) appends {"from": "w2", ...} via
  rumpun.collab.append_event from the env vars; argv ("read", "") prints
  all events. Run with: uv run python <workspace>/lane_tool.py start "..."
- Protocol: at start append kind=start; read the lane until w1 posts a
  kind=policy event, then write your marker tests to match w1's stated
  policy EXACTLY; append kind=claim naming the policy you coded against;
  at the end append kind=done with a one-line summary.
- Your notes.md must quote the policy event you coded against.

Rules: pytest only; no skips; no mocks; ruff clean, line-length 100,
py3.10+. notes.md: how to run, what you added, what you left out.
