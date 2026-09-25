# s91 w1 — fix issue #17: the akar H6 lock leaks under concurrency

The campaign's core write path has a 1-in-20 race window. This is the
most serious finding since the campaign began; the fix is the season.

## Ground truth (measured 2026-09-17)
- issue #17 (OPEN): the h6-loop repro runs 20 two-thread barrier
  rounds of same-id akar.append_record; round races show BOTH appends
  succeeding (1/20 on current main) — the lock leaks under concurrency
- the repro: the s18/w1-h6-loop.py corpus row; w2's probe:
  .rumpun/runs/s90/w2/probe_flock.py
- the ledger's integrity rests on append_record's atomicity

## Task
1. Reproduce at will: the barrier harness exists (the corpus repro;
   w2's probe_flock.py). Get the race to fire deterministically
   enough to test against (tighten the barrier if needed — the repro
   harness may be tuned; the CONTRACT cannot).
2. Read append_record's lock path (src/rumpun/akar.py, the H6
   history: the s18-era fix) and find the leak: the flock scope, the
   lock file identity, or the read-modify-write outside the lock.
3. Fix the smallest surface. The all-pass signature (0 races in 20
   barrier rounds) is the contract; well-formed sequential appends
   unchanged.
4. Pins: the race repro as a pins-file test (the barrier harness,
   tightened, N rounds asserting the all-pass signature) —
   tests/test_s91_w1_pins.py, _s91w1_ prefix.
5. Verify: the corpus row passes (the s49 pin's contract), 40+ barrier
   rounds clean across repeated runs, the full suite floor.

## Bounds
- Edits: src/rumpun/akar.py, tests/. notes.md REQUIRED: the leak, the
  fix, the before/after barrier counts.
