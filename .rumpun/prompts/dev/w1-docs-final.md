# Task: final README sync to the v0.9.0 surface (full README.md into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s10/w1. Write ONLY README.md,
notes.md into this workspace. Do not touch anything outside it.

Base your README.md on the CURRENT repo file /mnt/data/work/rumpun/README.md
(read it first) and the CURRENT /mnt/data/work/rumpun/src/rumpun/cli.py.

Changes, nothing else:
1. The "Not implemented yet" section must be REMOVED entirely: the stub
   registry is empty as of v0.9.0 — every parsed verb is implemented.
2. Add a short "Evolution loop" subsection to the quickstart (after harvest):
     rumpun evolve plan .rumpun/musim/s1.yaml      # draft the next season
     rumpun evolve apply .rumpun/musim/s2.yaml     # lint-gate the draft
     rumpun evolve approve .rumpun/musim/s2.yaml   # record approval in akar
     rumpun evolve reject .rumpun/musim/s2.yaml    # move draft to musim/rejected/, record P33
     rumpun evolve rollback s2                     # contain an applied season
   One line under each: what it does. rollback takes a season id, never runs
   git; reject takes a file.
3. Re-verify every command in the file against the current cli.py verb
   surface and flags; fix anything drifted. No version pins older than
   v0.9.0 anywhere. Do not invent verbs or flags.

Rules: no emoji, no marketing adjectives, every command runnable as
written. notes.md: what you re-verified and how.
