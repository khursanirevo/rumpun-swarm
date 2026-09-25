# s36 w2 — spec-first pins for the stall-resume logic

You are w2 in season s36 (repo root: the parent of this .rumpun tree). Read
src/rumpun/evolve.py, src/rumpun/engine.py (read_persisted_status), akar
record audit-25. You own tests/; w1 owns evolve.py. FILE TOOLS directly.
WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. Resume: drafting from a stopped_stall parent (fixture state) yields a
   successor whose benih budgets are ceil(parent x 1.5) and whose yaml
   header cites the parent's stall status.
2. No-stall parents: drafting from a completed parent is byte-identical
   to today's output (no budget change, no citation header).
3. Rounding: a 25-minute parent drafts 38-minute budgets (ceil).
4. Regression: the 171-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (171 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns evolve.py.

## Verify before finishing

Measured red set against current code in notes.md; the 171 existing
tests green.
