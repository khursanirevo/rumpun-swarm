# s62 w2 — spec-first pins for the salvage marker

You are w2 in season s62 (repo root: the parent of .rumpun). Read
src/rumpun/cli.py, src/rumpun/harvest.py, src/rumpun/audit.py, and ledger
records s59-harvest + usefulness-decade-5; the s61 pins
(tests/test_s61_w2_pins.py) are the shape precedent. You own tests/;
w1 owns the code. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Spec-first pins (red against current code)

1. The salvaged world: harvesting a stopped_stall fixture marks the
   verdict row (the salvage field) and the harvest record title
   "(salvaged)"; a completed fixture stays unmarked (subprocess, 240s
   bound).
2. The histogram split: after marking, a fresh audit over a fixture
   ledger with one salvaged and one completed win renders the split
   form ("2 WIN (1 salvaged)") or its agreed shape from w1's notes.
3. Immutability: the marking writes only new rows/records; existing
   ledger bytes stay identical (the directive seq 5 discipline).

## Constraints
- tests/ additions-only; subprocess pins, timeout bounded (240s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ - w1 owns the code; the harness merges.

## Verify before finishing
Measured red set in notes.md; the pins green at merge; the suite floor
holds.
