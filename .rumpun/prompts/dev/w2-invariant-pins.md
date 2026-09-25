# s34 w2 — spec-first pins for the falsify_required enforcement

You are w2 in season s34 (repo root: the parent of this .rumpun tree). Read
src/rumpun/lint.py, the campaign rumpun.yaml, akar records audit-23 +
usefulness-decade-3. You own tests/; w1 owns lint.py. FILE TOOLS directly.
WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. Enforcement: a season with zero reading phases in a campaign declaring
   falsify_required fails lint with an error naming the season.
2. Satisfaction: the lean shape (evaluate reading results.jsonl) passes.
3. Scope: a campaign without falsify_required in its invariants is
   unaffected (fixture with a bare invariants list).
4. Regression: the 161-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (161 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns lint.py.

## Verify before finishing

Measured red set against current code in notes.md; the 161 existing
tests green.
