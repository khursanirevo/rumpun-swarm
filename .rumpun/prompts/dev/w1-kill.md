# Task: fix the kill-marker defect in src/rumpun/engine.py (full file into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s4/w1. Write ONLY engine.py,
notes.md, lane_tool.py into this workspace. Do not touch anything outside it.

Base your engine.py on the CURRENT repo file
/mnt/data/work/rumpun/src/rumpun/engine.py (read it first; it already wires
collab lane env vars — keep that wiring intact).

Defect (found in s2, recorded in the akar ledger): agents that the season
engine kills at finalize (SIGTERM/SIGKILL of the process group) read back as
state "crashed" on any later snapshot. They leave no exit file and their pid
is dead. An agent the engine terminated is not a crashed agent.

Required fix, nothing else:
- _terminate gains the workspace path: _terminate(ws, pid). Before the first
  killpg, atomically write <ws>/"terminated" containing "terminated\n"
  (tmp file + os.replace).
- _agent_snap policy order: exit file -> exited/failed; else terminated
  marker -> "terminated" with exit_code None; else live -> running/stalled;
  else "crashed". If an exit file also exists, the exit file wins (it is
  more specific).
- Everything else stays behaviorally identical; all 15 tests in
  tests/test_rumpun.py must keep passing.

Collab lane (live dogfood — the point of this season):
- RUMPUN_LANE_FILE and RUMPUN_LANE_LOCK are exported to your process.
- Create lane_tool.py in your workspace: a small script whose argv is
  (kind, text) that appends {"from": "w1", "kind": kind, "text": text} via
  rumpun.collab.append_event using the env vars, and with argv ("read", "")
  prints all events via read_events. Run it with:
  uv run python <workspace>/lane_tool.py start "..."
- Protocol: at start append kind=start; BEFORE finishing engine.py append
  kind=policy stating your exact terminated-state policy so w2 can match its
  tests; then append kind=read is not a thing — run ("read", "") to see w2's
  events; at the end append kind=done with a one-line summary.
- Your notes.md must quote the policy event you posted and what w2 replied.

Rules: stdlib only. logging, never print (lane_tool may print: it is a CLI
tool). ruff clean, line-length 100, py3.10+.
