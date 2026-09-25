# s78 w1 — the board map: sync reads lanes first (the s76 recorded gap)

board --sync refused on s75 because no map wired its lanes to an issue.
Close that gap: the close emits the map, sync reads it first.

## Ground truth (measured 2026-09-17)
- board.py: issue_for_season (map first, then lane-title match),
  load_lane_map (.rumpun/board-map.json), lanes_for_season,
  harvest_comment_argv, close_issue_argv, sync_season
- the s76 gap: s75's lanes (board-create-live, panel-teeth) had no map
  and no lane-title issue match -> the documented BoardError
- issues #3-#5 are open board items; issue #1 is closed

## Task (spec-first is w2's lane; yours is the emission + wiring)
1. board.py grows: emit_lane_map(root, sid, issue_url) — writes
   .rumpun/board-map.json entries {lane title: issue url} for a
   season's lanes (merge, not clobber: existing entries survive).
2. cli wiring: `rumpun board --map <sid> <issue-url>` — the operator
   (or a season's close) records which issue a season's lanes answer;
   emits the map via emit_lane_map after an online check that the
   issue exists (rc-gated, one call).
3. Wire sync: before the lane-title fallback, the map entry is looked
   up and used (issue_for_season already prefers it — verify the
   wiring end to end and fix what is missing).
4. Live verification: `rumpun board --map s75 <issue #1 url>`, then
   `rumpun board --sync s75 --dry-run` renders the issue #1 comment
   and close (do NOT run the real sync for s75 — issue #1 is already
   closed; the dry-run is the proof). Record both outputs.

## Bounds
- Edits: src/rumpun/board.py, src/rumpun/cli.py, tests only. notes.md
  REQUIRED. The map file lives in the campaign's .rumpun (created only
  by this verb).
