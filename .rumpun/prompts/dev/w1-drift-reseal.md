# s48 w1 — the m5 repro re-sealed to current main

You are w1 in season s48 (repo root: the parent of this .rumpun tree). Read
tests/test_rumpun.py (the m5 repro: repro_m5_failed_exit and its DRIFT
classification in the audit), akar records audit-36 + s47-harvest. FILE
TOOLS directly. WRITE ONLY inside your workspace. 40 minutes.

## Deliverable: the m5 repro re-sealed

The repro asserts the pre-M5 contract (a both-agents-fail season exits 0).
The M5 change made it exit nonzero — the repro's assumptions moved, the
audit's DRIFT arming caught it honestly. Re-seal: the repro asserts the
M5 contract (a both-agents-fail season maps to nonzero with the honest
failed status). The repro's fixture season uses RUMPUN_YAML_FAIL and
SEASON_DUAL unchanged.

## Constraints

- The repro's fixture season unchanged (RUMPUN_YAML_FAIL + SEASON_DUAL).
- The re-sealed repro's assertion: the season's exit is nonzero AND the
  recorded status is failed (the M5 honest mapping).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — the repro is a test-file change.

## Verify before finishing

The re-sealed repro passes against current main (the M5 behavior). The
DRIFT arming's classification verified honest (the repro failed for its
own reason — the assumption moved, not a regression). Both in notes.md.
