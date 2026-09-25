# s112 w1 — the notes gate: the engine marks a notes-less exit

Twice now (s108 w1, s111 w1) a writer exited 0 without its notes.md and
only the brief's REQUIRED clause stood guard. The clause failed twice.
This lane makes the marking structural.

## Ground truth (measured 2026-09-20)
- the exit path: src/rumpun/engine.py writes the agent entry on writer
  exit (the state.json agents block: state/exit_code/seconds; the s111
  w1 unit exited 0 with no notes.md at .rumpun/runs/s111/w1/notes.md)
- results.jsonl rows carry unit/route/state/exit_code/seconds (the s111
  results.jsonl is the shape)
- notes.md sits at .rumpun/runs/<sid>/<w>/notes.md - gitignored live
  state, so pins embed or synthesize it (the check-s110 lesson: never
  copy from .rumpun/runs/)
- precedent: the brief clause failed twice; the gate must not depend on
  writer cooperation

## Task
1. Land the gate: when a writer's process exits, the engine checks
   .rumpun/runs/<sid>/<w>/notes.md; absent, the agent entry (and the
   results row) marks the unit INCOMPLETE instead of a bare exit 0 -
   state and exit code preserved, the notes gap named. Present, the
   entry is untouched. Pins red-first in tests/test_s112_notes_gate.py
   (synthesize the writer dirs in tmp; never copy live state).
2. Verify: solo pins green; full suite green vs the known reds (solo-run
   any new red); ruff clean. The real-campaign probe: the s111 state
   file shows w1 exited 0 pre-gate - do not rewrite sealed state; the
   pins carry the contract.
3. notes.md REQUIRED before ending the turn (your own lane proves the
   gate's reason). Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/engine.py, src/rumpun/collab.py (if the exit write
  lives there), tests/test_s112_notes_gate.py only. notes.md REQUIRED.
