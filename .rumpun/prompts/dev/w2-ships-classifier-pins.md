# s63 w2 — spec-first pins for the ships classifier

You are w2 in season s63 (repo root: the parent of .rumpun). Read
tools/artifact_check.py, .rumpun/ledger/2026-09-16_check-s61.md, and
ledger records s62-harvest + check-s61; the s62 pins
(tests/test_s62_w2_pins.py) are the shape precedent. You own tests/;
w1 owns tools/. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Spec-first pins (red against current code)

1. The s61 clause checks through: a ships row whose file-shaped token is
   run-time framed ("writes results.jsonl") with the artifact present in
   runs/<sid>/ yields MATCH, and the clause evidence records the
   classification (subprocess, 240s bound).
2. The genuine-missing case: a ships row claiming a committed file the
   tree lacks still yields DELTA exit 1 - the distinction is no bailout.
3. The classification is recorded: the clause evidence names which
   file-shaped tokens were runtime-checked vs committed-checked.

## Constraints
- tests/ additions-only; subprocess pins, timeout bounded (240s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ or tools/ - w1 owns tools/; the harness merges.

## Verify before finishing
Measured red set in notes.md; the pins green at merge; the suite floor
holds.
