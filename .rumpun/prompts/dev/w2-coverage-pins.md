# s52 w2 — green-check pins for the coverage finding

You are w2 in season s52 (repo root: the parent of this .rumpun tree).
Read src/rumpun/audit.py, tests/test_s43_w2_pins.py (the three standing
red pins you must turn green WITHOUT editing them), and akar records
audit-38 + s51-harvest. You own NEW tests/ additions only; the s43 pins
file is the ratified contract, not yours to touch. FILE TOOLS directly.
WRITE ONLY inside your workspace. 40 minutes.

## Pins

1. Turn the three s43 coverage pins green via the implementation (run
   them unchanged and record the green set) - the contract was written
   in s43; s52 owes it the emission.
2. One additions-only pin: mixed-matrix arithmetic - a matrix with 3
   PASS, 1 FAIL, 2 DRIFT, 40 SKIP yields the finding "corpus coverage:
   3 repro scripts PASS of 46 discovered (40 SKIP)" (the sums, not the
   uniform fixtures s43 used).
3. Measure and record the red set first (the emission is absent on
   current main), then green via the implementation at merge.

## Constraints
- tests/ additions-only vs the current repo files; the s43 pins file
  stays byte-identical.
- The pins call run_audit in-process; timeout bounded for any
  subprocess.
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ - w1 owns audit.py; the harness merges.

## Verify before finishing
Measured red set in notes.md; the s43 pins + the new pin green at merge;
the four known reds otherwise unchanged.
