# s48 w2 — spec-first pins for the m5 repro re-seal

You are w2 in season s48 (repo root: the parent of this .rumpun tree). Read
tests/test_rumpun.py (the m5 repro), akar records audit-36 + s47-harvest.
You own tests/; w1 owns the repro's re-seal. FILE TOOLS directly. WRITE
ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. The re-sealed repro: the both-agents-fail season maps to nonzero with
   the honest failed status (the pin asserts the M5 contract against the
   re-sealed repro).
2. The DRIFT classification verified honest: the audit's DRIFT row
   retired (the repro passes on current main), the arming was correct.

## Constraints

- tests additions-only vs the current repo file (188+ tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns the repro's re-seal.

## Verify before finishing

Measured red set against current code in notes.md; the suite green.
