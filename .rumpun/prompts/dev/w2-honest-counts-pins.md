# s39 w2 — spec-first pins for the honest season counts

You are w2 in season s39 (repo root: the parent of this .rumpun tree). Read
tools/usefulness_audit.py, akar records audit-28 + usefulness-decade-3. You
own tests/; w1 owns tools/. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Spec-first pins (red against current code)

1. The brief carries both counts: a fixture with 3 run + 2 drafted-only
   seasons produces the "3 run, 2 drafted-only, 5 total" headline.
2. The decade debt math is unchanged (total/10), so the trigger timing
   stays identical.
3. The stub-route capture includes the headline (the auditor sees it).
4. Regression: the 182-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (182 tests kept).
- The pins run the tool via subprocess against fixture roots.
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify tools/ — w1 owns it.

## Verify before finishing

Measured red set against current code in notes.md; the 182 existing
tests green.
