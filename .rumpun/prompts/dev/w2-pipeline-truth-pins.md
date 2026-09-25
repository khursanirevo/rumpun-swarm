# s61 w2 — pins for the pipeline's truth

You are w2 in season s61 (repo root: the parent of .rumpun). Read
src/rumpun/lint.py, src/rumpun/audit.py, src/rumpun/engine.py, and ledger
records s60-harvest + audit-41; the s60 pins
(tests/test_s60_w2_pins.py) are the shape precedent. You own tests/;
w1 owns the code. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Spec-first pins (red against current code)

1. Whatever route w1 takes, the pin holds the NEW truth: either a
   season run through the pipeline path lands results.jsonl in its
   ledger, or a season yaml without the pipeline block lints and starts.
2. The finding retires honestly: after the change, a fresh audit over a
   synthetic campaign no longer arms the phase-liveness candidate for
   the changed seasons (or the exercised season counts in the
   numerator).
3. No regression: the falsify gate still demands a reachable reader for
   any DECLARED write; the stall record shape is untouched.

## Constraints
- tests/ additions-only; the pins run the real verbs via subprocess,
  timeout bounded.
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ - w1 owns the code; the harness merges.

## Verify before finishing
Measured red set in notes.md; the pins green at merge; the suite floor
holds.
