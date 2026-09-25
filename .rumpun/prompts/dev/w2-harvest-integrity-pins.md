# s40 w2 — spec-first pins for harvest integrity

You are w2 in season s40 (repo root: the parent of this .rumpun tree). Read
src/rumpun/harvest.py, src/rumpun/engine.py (read_persisted_status), akar
records audit-29 + s29-harvest. You own tests/; w1 owns harvest.py. FILE
TOOLS directly. WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. M4 full: harvest of a RUNNING season raises AkarError naming the
   season and its status; no id consumed; no verdicts row written.
2. Write order: an injected akar failure between the appends leaves no
   verdicts row (the row cannot strand without its record).
3. Regression: a terminal season with its season row present still
   refuses a second harvest (the s21 pin keeps holding).
4. Regression: the 185-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (185 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns harvest.py.

## Verify before finishing

Measured red set against current code in notes.md; the 185 existing
tests green.
