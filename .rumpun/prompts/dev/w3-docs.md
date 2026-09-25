# Task: final README sync (full README.md into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s6/w3. Write ONLY README.md,
notes.md, lane_tool.py into this workspace. Do not touch anything outside it.

Base your README.md on the CURRENT repo file /mnt/data/work/rumpun/README.md
(read it first) and the CURRENT /mnt/data/work/rumpun/src/rumpun/cli.py.

Changes, nothing else:
1. Add `rumpun season show s1` to the quickstart right after board, with one
   line: prints the season detail plus each agent's deliverable files; --json
   for the machine form. (The verb lands in this same season, v0.6.0.)
2. Remove `season show` from the "Not implemented yet" table.
3. Re-verify every command in the README against the current cli.py verb
   surface and flags; fix anything drifted. Do not invent verbs or flags.
4. Bump the doc reference: the cli docstring says v0.6.0; the README must
   not pin an old version anywhere.

Collab lane (protocol v2, NON-BLOCKING — evidence gathering only):
- RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK are exported to you.
- lane_tool.py: argv (kind, text) appends {"from": "w3", "kind": kind,
  "text": text} via rumpun.collab.append_event from the env vars; argv
  ("read", "") prints events. Post kind=start and kind=done. Never wait
  on anyone.

Rules: no emoji, no marketing adjectives, every command runnable as
written. ruff clean, line-length 100 (markdown lines may wrap freely).
notes.md: what you re-verified and how.
