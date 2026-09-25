# s79 w1 — fix issue #2: append_record citations lint cannot resolve

The first board-pulled season: the issue is the scope. Read it, fix it,
let the lifecycle close it.

## Ground truth (measured 2026-09-17)
- issue #2 on khursanirevo/rumpun: "append_record writes records where
  lint cannot resolve citations (v0.11.0)" — OPEN, filed from real use
- board.py: emit_lane_map, sync_season, the argv builders; the map
  works (s78); the s75 dry-run proved the loop live
- the season's own close will exercise the loop for real: board --map
  s79 <issue #2 url> at close, then the harness's sync closes it

## Task
1. Read issue #2 (`gh issue view 2 -R khursanirevo/rumpun`) and
   reproduce the defect: append_record's emitted citations vs what
   lint's citation resolver accepts. Find the exact divergence (a
   format mismatch, not a lint bug — unless the evidence says
   otherwise; the issue text is the spec).
2. Fix append_record's citation emission (or the resolver, per the
   evidence). Smallest change set. The existing behavior for
   well-formed citations stays.
3. Pins (tests/test_s79_w1_pins.py, _s79w1_ prefix, offline): the
   reproduced divergence (red-shaped → green), the fix's contract,
   and the well-formed path unchanged.
4. `rumpun board --map s79 <issue #2 url>` so the close's sync finds
   the season. Re-run your pins + the board pins (s78's) solo; green.

## Bounds
- Edits: src/rumpun/ (the two modules the evidence names), tests/.
- notes.md REQUIRED: the divergence, the fix, the pin list.
