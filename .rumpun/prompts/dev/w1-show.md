# Task: implement rumpun season show (full cli.py into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s6/w1. Write ONLY cli.py,
notes.md, lane_tool.py into this workspace. Do not touch anything outside it.

Base your cli.py on the CURRENT repo file
/mnt/data/work/rumpun/src/rumpun/cli.py (read it first; keep every behavior
and all 19 tests passing; do not edit tests/).

Replace the season show stub with a real verb:
  rumpun season show <id> [--json]
- Human output: one status line (reuse the _render_state shape), then one
  line per agent with its deliverables: files in the agent workspace that
  are NOT engine bookkeeping (exclude agent.log, exit, prompt.md,
  prompt-meta.yaml, state.json, terminated, terminated.tmp, __pycache__).
- If .rumpun/rimba/<id>/_season/lane-*.jsonl exists, print one line per
  lane: file name and event count.
- --json: {"id","status","started_at","ended_at","agents":{...},"deliverables":
  {agent: [names]},"lanes": {file: count}} — read_status plus the
  deliverable/lane scan; no other keys.
- Unknown id -> EngineError via read_status (existing behavior). Remove
  "show" from SEASON_STUBS. Docstring version note becomes v0.6.0.

Collab lane (protocol v2, NON-BLOCKING — evidence gathering only):
- RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK are exported to you.
- lane_tool.py: argv (kind, text) appends {"from": "w1", "kind": kind,
  "text": text} via rumpun.collab.append_event from the env vars; argv
  ("read", "") prints events. Post kind=start, kind=policy (your exact
  output contract), kind=done. Never wait on w2.

Rules: stdlib only; the verb's own output may print. ruff clean,
line-length 100, py3.10+. notes.md: the output contract you posted.
