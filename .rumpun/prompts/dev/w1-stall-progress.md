# s60 w1 — stall detection counts real progress

You are w1 in season s60 (repo root: the parent of this .rumpun tree).
Read src/rumpun/engine.py (the stall watcher, the progress-event
classification), the s59 stop record (.rumpun/runs/s59/_season/), and
ledger records s59's harvest + audit-40. FILE TOOLS directly. WRITE ONLY
inside your workspace EXCEPT minimal documented engine.py changes.
40 minutes.

## Deliverables (workspace copies; the harness merges)

1. The stall watcher counts file-tool progress: a season whose agent
   stream shows recent file writes (or any parsed tool_use event) is
   making progress - the stall clock resets on those events, not only
   on stream output. The s59 kill (w2 terminated mid-write while
   producing a 274-line pins file) must be impossible under the new
   rule.
2. The stop record names the progress rule: a stopped_stall season's
   state or log line records which events counted and the last-progress
   age at the stop, so a stall stop is auditable after the fact.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- Additive: the suite floor holds; the known race flakes stay the only reds.
- Do not weaken genuine liveness: a dead stream with no events at all
  still stalls.

## Verify before finishing
Reproduce the s59 shape (a writer quiet on stdout, busy on files) in a
stub run: it completes. A truly dead stub still stalls. notes.md.
