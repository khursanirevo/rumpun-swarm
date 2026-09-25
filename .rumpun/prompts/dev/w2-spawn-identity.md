# s124 w2 — the running state reconciles against live processes

The restart scar: state said "running", the writers were dead, and
nothing reconciled the record against reality until a human looked.

## Ground truth (measured 2026-09-20)
- the machinery: src/rumpun/engine.py (the snap carries pid and
  proc_start; the live reader recomputes agent snaps from /proc for
  running seasons per the M1/P36 split)
- the scar: the s109 restart - a dead runner stayed "running" in the
  durable state; the reaper (the sibling's PR #34) handles boot, the
  reconciliation surface is the pin's subject
- the rule: a snap whose pid or proc_start no longer matches /proc
  reads crashed or terminated, never running - and the status output
  names the reconciliation
- fixture discipline: inject fake /proc data in fixtures; never test
  against the real process table

## Task
1. Land the pin: the reconciliation (pid/proc_start mismatch ->
  crashed, with the status output naming it) is pinned red-first in
  tests/test_s124_spawn_identity.py (fake /proc fixtures in tmp; the
  real process table never touched). If the behavior already holds,
  the pins document it and the red-first capture covers the
  docstring/contract shape only - the season still owes its red runs
  for anything newly written.
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/engine.py, tests/test_s124_spawn_identity.py
  only. notes.md REQUIRED.
