# s49 w2 — spec-first pins for the superseded-repro skip

You are w2 in season s49 (repo root: the parent of this .rumpun tree). Read
tools/replay_corpus.py, akar records audit-37 + s48-harvest. You own
tests/; w1 owns the runner. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Spec-first pins (red against current code)

1. The skip: the runner's matrix carries a SKIP row for the s22 archived
   repro citing the supersession (the s48 re-seal at evidence/s48/).
2. The DRIFT row for that script retires from the audit's candidates
   (the audit --corpus after the skip carries no s22 m5 DRIFT candidate).
3. The other five scripts still run and pass.
4. Regression: the 188-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (188 tests kept).
- The pins run the runner via subprocess, timeout bounded (120s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify tools/ — w1 owns the runner.

## Verify before finishing

Measured red set against current code in notes.md; the 188 existing
tests green.
