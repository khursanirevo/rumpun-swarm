# s135 w1 — an armed timer cannot strand a lane unnoticed

Issue #44 (the s85 incident): a writer exited with a background wake
timer armed; the dependent verify lane's results were lost and nothing
marked the exit.

## Ground truth (measured 2026-09-21)
- the exit read: src/rumpun/engine.py _agent_snap (the s112 incomplete
  key and the s124 reconciled key are the additive precedents; the
  failed and crashed vocabulary unchanged)
- the loss shape: a writer spawns a background wake timer (its own
  harness), exits rc 0, and the dependent verification never runs -
  the bare exit hides the stranded work
- the honest mark: an additive key naming the stranded-work risk when
  the exit evidence shows an armed timer or an unverified dependent
  lane; the s112 gate keys on what the exit evidence shows
- fixture discipline: tmp fixtures; no real timers in tests

## Task
1. Land the guard: the exit read marks the stranded-work risk when the
   lane's evidence shows it (define the detection honestly: what the
   engine can see at exit read); rows without it stay byte-identical.
   Pins red-first in tests/test_s135_background_timer.py (tmp
   fixtures).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/engine.py, tests/test_s135_background_timer.py
  only. notes.md REQUIRED.
