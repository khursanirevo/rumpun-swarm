# s35 w2 — spec-first pins for the verdict-consistency cross-check

You are w2 in season s35 (repo root: the parent of this .rumpun tree). Read
src/rumpun/audit.py, akar records audit-24 + usefulness-decade-3. You own
tests/; w1 owns audit.py. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Spec-first pins (red against current code)

1. Mismatch arms: a WIN season with a FAIL unit row arms exactly one
   candidate citing the season and the failing unit.
2. Consistent seasons arm nothing (WIN rows under WIN season).
3. No results rows: unaffected (no candidate, no crash).
4. Multiple FAIL rows: still exactly ONE mismatch candidate per season.
5. Regression: the 166-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (166 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns audit.py.

## Verify before finishing

Measured red set against current code in notes.md; the 166 existing
tests green.
