# s38 w2 — spec-first pins for the loop-propagation steps

You are w2 in season s38 (repo root: the parent of this .rumpun tree). Read
tools/coldstart_check.py (w1's s37 checker), akar records audit-27 +
usefulness-decade-3. You own tests/; w1 owns tools/. FILE TOOLS directly.
WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. Propagation: the extended checker completes steps through s2's harvest
   (the summary reports the extended step count, all PASS).
2. s2 artifacts exist in the temp dir after the run: musim/s2.yaml, s2's
   verdicts row, s2's akar harvest record.
3. A propagation failure fails honestly: with the evolve step sabotaged
   (a stub that makes draft planning fail), the checker exits nonzero
   naming the failed step.
4. Isolation: the repo's own .rumpun stays sha-verified untouched.
5. Regression: the 178-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (178 tests kept).
- The pins run the checker via subprocess, timeout bounded (180s for the
  extended run), no wall-clock asserts beyond it.
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ or tools/ — w1 owns the checker.

## Verify before finishing

Measured red set against current code in notes.md; the 178 existing
tests green.
