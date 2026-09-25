# s123 w2 — the results row attests the lane's commit

Writers commit now; the run record cannot say which commit a lane
produced. The engine can.

## Ground truth (measured 2026-09-20)
- the row builder: src/rumpun/engine.py _agent_snap and
  _write_results (the s112 gate pattern: additive keys, measured state
  untouched)
- the mechanism: the engine records the season's start HEAD at spawn;
  at exit read, a lane whose HEAD moved past it carries the new HEAD
  as an additive commit key on the snap and the results row - the
  attestation names the commit without judging it
- the s112 precedent: additive keys only, the failed and crashed
  vocabulary unchanged, rows without the key keep their shape
- fixture discipline: a tmp git repo in the fixture; the real
  campaign never written in tests

## Task
1. Land the attestation: the snap records the start HEAD at spawn;
   at exit, HEAD moved -> the snap and the results row carry the
   additive commit key. No move -> nothing changes. Pins red-first in
   tests/test_s123_commit_attestation.py (a tmp git repo fixture).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/engine.py, tests/test_s123_commit_attestation.py
  only. notes.md REQUIRED.
