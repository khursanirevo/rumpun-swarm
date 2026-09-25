# s124 w1 — the lane heartbeat: silence becomes an event

A stalled lane is silent; the restart scar sat with state at "running"
until a human noticed. Silence should be visible.

## Ground truth (measured 2026-09-20)
- the tick: src/rumpun/loop.py (the close-prep and the draft hand-off
  already ride it)
- the stall data: the state snap carries stall_s and last_progress;
  a lane past its stall window with no progress is the signal
- the surfaces: the events dir (.rumpun/events/, the append-only
  event convention) and the report (src/rumpun/report.py, the s113
  marks precedent)
- fixture discipline: tmp campaigns; no real event writes in tests

## Task
1. Land the heartbeat: at a tick, a running lane past its stall window
   with no progress emits a named event (season, lane, last-progress)
   and the report renders the mark; idempotent per lane-stall. Pins
   red-first in tests/test_s124_lane_heartbeat.py (tmp fixtures).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/loop.py, src/rumpun/report.py,
  tests/test_s124_lane_heartbeat.py only. notes.md REQUIRED.
