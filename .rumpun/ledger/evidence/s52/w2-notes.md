# s52 w2 — green-check pins for the coverage finding

Worker: w2, season s52, repo /mnt/data/work/rumpun @ main acd412e.
Scope: NEW tests/ additions only; tests/test_s43_w2_pins.py untouched
(git diff clean, verified). src/ untouched — w1 owns audit.py; the
harness merges.

## Measured red set — current main (acd412e), 2026-09-16

Command (repo root): `.venv/bin/python -m pytest tests/test_s43_w2_pins.py`
Log: /tmp/s52w2_red_baseline.txt — 3 failed, 5 passed in 0.46s

- RED `test_fresh_matrix_coverage_finding_counts_all_rows` (s43 pin 1)
- RED `test_coverage_gap_is_finding_never_candidate` (s43 pin 2)
- RED `test_coverage_zero_pass_is_honest` (s43 pin 3)
- GREEN pins 4-8: drift arming x3, falsify naming, reachable-reader guard

Failure shape (the contracted gap, not a fixture error): the record emits

```
corpus: fresh matrix, 0 PASS, 0 FAIL, 0 DRIFT, 53 SKIP — all green on main, no candidates
```

— no coverage line. The emission is absent on main. audit-38 shows the
same blind spot on the real ledger: `5 PASS, 0 FAIL, 0 DRIFT, 97 SKIP —
all green on main`.

## New pin (additions-only)

File: `tests/test_s52_w2_pins.py` (this workspace; graft to repo tests/
as-is — self-contained module, `_s52w2_` helpers, no collisions).

`test_mixed_matrix_coverage_finding_sums_all_verdicts`:

- Matrix: 3 PASS + 1 FAIL + 2 DRIFT + 40 SKIP = 46 discovered (the sums,
  where the s43 fixtures were uniform PASS+SKIP).
- Requires exactly one coverage finding:
  `corpus coverage: 3 repro scripts PASS of 46 discovered (40 SKIP)`
  — the denominator must sum EVERY verdict class, so a PASS+SKIP-only
  sum (43) fails the pin.
- The finding coexists with the corpus regression candidate the FAIL row
  arms (cites repro/fail_0.py), and the record must not claim
  "all green on main" while 43 of 46 discovered scripts do not pass.
- Calls run_audit in-process; no subprocess, so no timeout to bound.
- Measured red on main: `expected one coverage finding, got: []`
  (/tmp/s52w2_pin_red.txt) — red for the right reason (missing emission,
  not a fixture/import error). `1 failed in 0.42s`.
- ruff clean: `~/.local/bin/ruff check --no-respect-gitignore` → All
  checks passed (repo line-length config applies via pyproject walk-up).

## Measured green set — 2026-09-16

w1's emission landed in the repo working tree mid-session (uncommitted
` M src/rumpun/audit.py`, HEAD still acd412e); a single armed wait fired
LANDED_REPO at 0s. The emission (audit.py:755-762) writes one line with
denominator len(matrix_rows) — the sum of every verdict class — and
retires the "all green on main" claim on any SKIP, FAIL, or DRIFT.

Command (repo root): `.venv/bin/python -m pytest tests/test_s43_w2_pins.py
.rumpun/runs/s52/w2/tests/test_s52_w2_pins.py` — Log:
/tmp/s52w2_green_set.txt — **9 passed in 0.42s, exit 0** ✅

- GREEN the three s43 coverage pins, run unchanged (byte-identical file)
- GREEN the new mixed-matrix pin: exact line
  `corpus coverage: 3 repro scripts PASS of 46 discovered (40 SKIP)` —
  denominator sums every verdict class (a PASS+SKIP-only sum of 43 fails
  the pin), the finding coexists with the corpus regression candidate the
  FAIL row arms, and no "all green on main" claim appears
- GREEN s43 pins 4-8 (drift arming x3, falsify naming, reachable guard)

## Full suite — four known reds check

Run once after the emission landed (repo root, `pytest tests/`): log
/tmp/s52w2_full_suite.txt — running in background, outcome appended below
on its completion notification.

## Status

- Red set: measured ✅ (s43 pins 1-3 + the new pin, right reasons above)
- New pin: written, red for the right reason, ruff clean ✅
- Green set: pending w1's audit.py. w1 was still running at first check
  (state.json live, log growing) and HEAD had not moved at second check.
  One single-shot armed wait for w1's landing follows this write; if the
  code appears in the repo or w1's workspace, the green set is measured
  and recorded here. If it times out, the green verification happens at
  the harness merge per the procedure above.
