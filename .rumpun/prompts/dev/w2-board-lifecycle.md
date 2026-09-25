# s74 w2 — the board lifecycle: harvest closes its issue (seq 14 loop)

The board lands this season (w1's lane, scope live). Your slice: the
lifecycle — a sealed harvest reaches back to its issue, comments the
record, and closes the loop. Offline-pinned; live gh stays in w1's lane.

## Ground truth
- board.py: OWNER, REPO, ITEM_LIST_ARGV, parse_item_list,
  issue_create_argv, item_add_argv, pickup (the live seam)
- the harvest record: .rumpun/ledger/<date>_s<N>-harvest.md, sealed,
  carries verdict + implies; issues carry the season's lane title
- s73 proved the pattern to copy: argv builders pinned offline, the
  live seam bounded and pluggable

## Task (spec-first, pins in tests/test_s74_w2_pins.py, _s74w2_ prefix)
1. board.py grows: harvest_comment_argv(issue_url, record_path) —
   argv that comments the issue with the harvest record's verbatim
   body; close_issue_argv(issue_url) — argv that closes it. Pure
   builders, pinned argv-exact.
2. board.py grows: issue_for_season(root, sid) — reads the campaign's
   lane map (a committed .rumpun/board-map.json or falls back to the
   issue title match on pickup() rows) and returns the issue url a
   season's harvest should close; None when unmapped.
3. `rumpun board --sync <sid> --dry-run`: renders exactly what would
   be commented and closed, writing nothing. Without --dry-run it runs
   the argv through the bounded live seam (the w1-style pattern).
4. Pins: builders argv-exact; issue_for_season against a fixture
   board-map and fixture pickup rows; --sync --dry-run writes nothing
   (byte-check the rendered output).

## Bounds
- Edits: src/rumpun/board.py, cli wiring, tests/. notes.md REQUIRED.
  No real gh call in pins; one live --sync --dry-run is fine.
