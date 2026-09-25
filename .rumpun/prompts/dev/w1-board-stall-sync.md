# s125 w1 — the board carries the stall

The heartbeat emits the stall events and the report renders them; the
board is where the operator reads. The sync should carry the stall.

## Ground truth (measured 2026-09-20)
- the sync: src/rumpun/board.py (the s119 ledger-verdict mirror,
  idempotent, nothing invented)
- the stall truth: the heartbeat events (.rumpun/events/, kind
  lane-stalled) and the report's stall marks (src/rumpun/report.py
  _stall_marks)
- fixture discipline: the pure mirror logic over fixture events in
  tmp; no network in pins; the gh write path rides the designed seam

## Task
1. Extend the sync: a season whose lanes carry stall events gets the
   stall on its card after a sync (naming the lane and the
   last-progress); idempotent (a second sync changes nothing); no
   stall, no mark. Pins red-first in tests/test_s125_board_stall_sync.py
   (fixture events in tmp).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/board.py, tests/test_s125_board_stall_sync.py
  only. notes.md REQUIRED.
