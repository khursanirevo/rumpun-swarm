# Task: README sync for the lean pipeline (full README.md into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s12/w2. Write ONLY README.md,
notes.md, lane_tool.py into this workspace. Do not touch anything outside it.

Base your README.md on the CURRENT repo file /mnt/data/work/rumpun/README.md
(read it first) and the CURRENT /mnt/data/work/rumpun/src/rumpun/scaffold.py.

Changes, nothing else:
1. In "Season lifecycle", replace any 7-phase description with the lean
   default: a season declares two phases — execute (the benih build the
   step) and evaluate (the judge writes verdicts) — and explains in one line
   why: reflection (s11's audit) found the longer declared pipeline
   unexercised; extra phases can be declared per-season when a task needs
   them.
2. Anywhere the README names phases, make it match the 2-phase scaffold.
3. Re-verify every command against the current cli.py verb surface; fix
   anything drifted. No new verbs, no version pin changes.

Collab lane (protocol v2, NON-BLOCKING): post kind=start, kind=policy (what
you claim about the lifecycle), kind=done via lane_tool.py from
RUMPUN_LANE_FILE/RUMPUN_LANE_LOCK. Never wait on w1.

Rules: no emoji, no marketing adjectives. ruff clean, line-length 100.
notes.md: what you re-verified.
