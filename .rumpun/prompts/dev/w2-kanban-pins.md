# s66 w2 — spec-first pins for the kanban verb

You are w2 in season s66 (repo root: the parent of .rumpun). Read
src/rumpun/cli.py, src/rumpun/audit.py, src/rumpun/harvest.py, and ledger
records s65-harvest + audit-42 + directives seq 7/8/10; the s65 pins
(tests/test_s65_w2_pins.py) are the shape precedent. You own tests/;
w1 owns cli.py + scaffold. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Spec-first pins (red against current code)

1. `rumpun kanban` renders all four columns from a fixture campaign
   (backlog naming an armed candidate, doing naming the running season,
   done counting harvested seasons with salvage marks) - subprocess,
   240s bound.
2. NEED HUMAN carries the four-sentence card format (directive seq 8):
   what happened, what needs doing, why human, what happens if nobody
   acts - the unset-cap card renders all four.
3. No new state file: the verb derives everything from the ledger, runs
   state, and directives; a fresh campaign with no history renders
   empty columns and exits 0.

## Constraints
- tests/ additions-only; subprocess pins, timeout bounded (240s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ - w1 owns cli.py + scaffold; the harness merges.

## Verify before finishing
Measured red set in notes.md; the pins green at merge; the suite floor
holds.
