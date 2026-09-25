# s32 w2 — spec-first pins for the band-mask guard

You are w2 in season s32 (repo root: the parent of this .rumpun tree). Read
src/rumpun/lint.py, src/rumpun/audit.py, akar records audit-20 + audit-19.
You own tests/; w1 owns lint.py + audit.py. FILE TOOLS directly. WRITE
ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. Band-mask warning: a modules_integrated season whose expected_band
   lacks integration tokens produces exactly one WARNING naming the sid.
2. Silent pass: the same season with integration tokens in the band
   produces no new warning.
3. Non-modules metrics: a different metric with a vague band produces
   no warning (the guard is scoped to the integration metric).
4. Recalibrate retirement: the audit's recalibrate candidate fires only
   when a warned season sits in the audited window (fixture: compliant
   bands -> no candidate; warned band -> candidate).
5. Regression: the 145-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (145 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns lint.py + audit.py.

## Verify before finishing

Measured red set against current code in notes.md; the 145 existing
tests green.
