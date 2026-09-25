# s119 w1 — the loop prepares the close, the worker confirms it

Directive 17 lives in the operator's session: after every close, the
session seeds and launches the next season. The loop verb should at
least see the finished season and prepare the close - never perform it.

## Ground truth (measured 2026-09-20)
- the loop verb: src/rumpun/loop.py (the operator's khursani swarm
  runs `rumpun loop --exec`; the sibling's PR #34 reaper lives here)
- the completed state: engine.read_status returns status completed
  with no <sid>-harvest record in .rumpun/ledger/ (akar.declared_ids
  answers)
- the hard rule: the loop NEVER runs harvest, evolve, or git - the
  close protocol's suite run, DESIGN entry, and honest verdict prose
  are the close worker's judgment, not a script's
- fixture discipline: tmp campaigns; the harvest verb never runs in a
  test; no real ledger writes

## Task
1. Land the close-prep: at a loop tick, a season in completed state
   with no harvest record seals a close-prep record (the season id,
   the completed-at stamp, a named line reserving the verdict and the
   DESIGN entry to the close worker). Idempotent: one record per
   season. Pins red-first in tests/test_s119_loop_close_prep.py
   (fixture campaigns in tmp; no real ledger writes).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/loop.py, tests/test_s119_loop_close_prep.py only.
  notes.md REQUIRED.
