# s90 w2 — the s49 repro pin: stabilize the newest load-flake class

The s49 repro pin runs five real repro subprocesses and flakes under
the swarm's load (failed twice in gates, solo-green in 9.5s both
times). Make it swarm-tolerant without weakening the contract.

## Ground truth (measured 2026-09-17, the RESUME known-reds entry)
- test_s49_w2_pins.py::test_s49w2_other_five_repros_still_pass runs
  the five repros from S49W2_OTHER_REPROS against the corpus rows
- the failure mode: under swarm load a repro's subprocess timing
  wobbles (the corpus rows record timing-adjacent verdicts)
- the campaign's flake family: the race pins, the s38 coldstart pin,
  now this — all solo-green

## Task
1. Read the pin and one wobbled repro to find the exact wobble
   (a timeout too tight? a timing-adjacent assertion? output racing a
   write?). Evidence first: reproduce the wobble shape from the two
   gate logs if they still exist, else from a stress run.
2. Stabilize minimally per the evidence: the least contract-weakening
   change that makes the pin load-tolerant (a generous timeout, a
   retry-once-with-evidence, a deterministic ordering) — the contract
   "the five repros still pass" stays asserted.
3. Pins: the stabilized pin passes solo AND under an induced load
   (a background wobbler spawned in the pin's fixture, cleaned up
   after) — prove the stabilization, don't hope for it.
4. notes.md REQUIRED: the wobble shape, the fix, the load-test
   evidence.

## Bounds
- Edits: tests/test_s49_w2_pins.py + the pin's own fixture helpers
  only. If the wobble is a REAL product defect (a repro genuinely
  races), file the precise issue instead of stabilizing the pin and
  stop honestly. notes.md REQUIRED.
