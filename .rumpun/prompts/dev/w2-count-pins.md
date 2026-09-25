# s64 w2 — spec-first pins for the count honesty

You are w2 in season s64 (repo root: the parent of .rumpun). Read
tools/usefulness_audit.py, src/rumpun/audit.py, and ledger records
usefulness-decade-5 + audit-41; the s63 pins
(tests/test_s63_w2_pins.py) are the shape precedent. You own tests/;
w1 owns tools/. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Spec-first pins (red against current code)

1. The counts sum to the season total: a fixture ledger of 6 seasons
   (4 verdict rows, 1 running, 1 missing) yields 4 classified + 1
   running + 1 missing, and the counts say so - nothing blurs.
2. The salvaged split: a fixture with one stopped_stall-salvaged WIN
   shows the split in the counts (the s62 marks read through).
3. The real ledger's counts are reported, not asserted - the pin
   captures the composer's real-ledger run for the notes; the fixture
   asserts the arithmetic.

## Constraints
- tests/ additions-only; subprocess pins, timeout bounded (240s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ or tools/ - w1 owns tools/; the harness merges.

## Verify before finishing
Measured red set in notes.md; the pins green at merge; the suite floor
holds.
