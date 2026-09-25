# Task: README sync for the v0.7.0 surface (full README.md into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s7/w2. Write ONLY README.md,
notes.md, lane_tool.py into this workspace. Do not touch anything outside it.

Base your README.md on the CURRENT repo file /mnt/data/work/rumpun/README.md
(read it first) and the CURRENT /mnt/data/work/rumpun/src/rumpun/cli.py.

Changes, nothing else:
1. Add `rumpun season show s1` to the quickstart after board: prints the
   season detail plus each agent's deliverable files; --json for the
   machine form. (The verb exists in v0.6.0.)
2. Add `rumpun direct "one line of operator intent"` to the quickstart
   before season start: appends a pending directive to the akar ledger;
   `rumpun direct --list` shows them. (Lands in v0.7.0, this season.)
3. The "Not implemented yet" table must end up listing exactly:
   evolve approve, evolve reject, evolve rollback. Remove everything else.
4. Re-verify every command against the current cli.py verb surface; fix
   anything drifted. Do not invent verbs or flags. No version pins older
   than v0.7.0 anywhere.

Collab lane (protocol v2, NON-BLOCKING — evidence gathering only):
- RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK are exported to you.
- lane_tool.py: argv (kind, text) appends {"from": "w2", "kind": kind,
  "text": text} via rumpun.collab.append_event from the env vars; argv
  ("read", "") prints events. Post kind=start and kind=done. Never wait
  on anyone.

Rules: no emoji, no marketing adjectives, every command runnable as
written. ruff clean, line-length 100. notes.md: what you re-verified.
