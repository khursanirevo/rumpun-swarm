# s78 w2 — pins for the board map (spec-first)

w1 lands emit_lane_map, the --map verb, and the sync wiring. Pin the
contract offline: the map's shape, the merge semantics, the lookup
order, and the dry-run behavior.

## Ground truth
- board.py: issue_for_season (map first, lane-title match second),
  load_lane_map, lanes_for_season; the s76 gap: unmapped lanes
  BoardError'd sync (documented, s76 notes)
- board-map.json: flat {lane title: issue url}, merge-not-clobber

## Task (spec-first, pins in tests/test_s78_w2_pins.py, _s78w2_ prefix)
1. Pin emit_lane_map: writes valid JSON, merges with existing entries
   (existing keys survive), creates the file when absent, and is
   idempotent on re-run.
2. Pin issue_for_season order: a map entry wins over a lane-title
   pickup match; no map entry falls through to pickup; neither ->
   None (sync then BoardErrors, the s76 behavior).
3. Pin the --map verb's offline shape: the argv/rc contract of its
   issue-existence check (rc nonzero -> no map write), and that the
   map write happens only after the check passes.
4. Pin the s75 dry-run shape: with the map seeded in a fixture, the
   dry-run render names issue #1 and the sealed record, writing
   nothing.
5. notes.md REQUIRED: what you pinned, what you left to w1's live run.

## Bounds
- Edits: src/rumpun/board.py, tests/. No cli.py unless w1's verb
  demands a shared helper (coordinate through the shared build lane).
  No live gh call in pins.
