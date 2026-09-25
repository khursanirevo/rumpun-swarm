# s65 w2 — spec-first pins for the containment gate

You are w2 in season s65 (repo root: the parent of .rumpun). Read
src/rumpun/engine.py, src/rumpun/cli.py, and ledger records s64-harvest +
check-s63 + usefulness-decade-5; the s64 pins
(tests/test_s64_w2_pins.py) are the shape precedent. You own tests/;
w1 owns the code. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Spec-first pins (red against current code)

1. The block: with a DELTA check record as the newest check for the
   previous season, `rumpun season start` refuses nonzero, naming the
   record (subprocess, 240s bound).
2. The releases: a later VERIFIED check for that season releases the
   block, and a waiver record naming the check releases it too - both
   starts succeed.
3. Clean campaigns start normally: no check records at all is not a
   block (first seasons, fresh campaigns).

## Constraints
- tests/ additions-only; subprocess pins, timeout bounded (240s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ - w1 owns the code; the harness merges.

## Verify before finishing
Measured red set in notes.md; the pins green at merge; the suite floor
holds.
