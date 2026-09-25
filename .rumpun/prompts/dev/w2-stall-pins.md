# s60 w2 — spec-first pins for stall progress

You are w2 in season s60 (repo root: the parent of .rumpun). Read
src/rumpun/engine.py (the stall watcher), the s59 stop record, and ledger
records s59's harvest + audit-40; the s55 pins (tests/test_s55_w2_pins.py)
are the shape precedent. You own tests/; w1 owns engine.py. FILE TOOLS
directly. WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. A stub agent that only writes files (no stdout activity beyond the
   writes) survives a stall window that would kill it today: the season
   completes instead of stopped_stall.
2. A dead agent (no events at all) still stalls: the rule counts
   progress, it does not abolish the stall.
3. The stop record names the rule: a stopped_stall fixture records the
   last-progress age and the counted event classes at the stop.

## Constraints
- tests/ additions-only; stub agents, no wall-clock assertions beyond
  the existing patterns.
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ - w1 owns engine.py; the harness merges.

## Verify before finishing
Measured red set in notes.md; the pins green at merge; the suite floor
holds.
