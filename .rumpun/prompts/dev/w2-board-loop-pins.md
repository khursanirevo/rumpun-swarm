# s79 w2 — pins for the first board-pulled close (the loop's proof)

w1 fixes issue #2 and maps the season. Your slice: pin the loop's
end-to-end contract offline — the season that pulls an issue also
closes it through the map, with the sealed record as the comment.

## Ground truth
- board.py: emit_lane_map, issue_exists_argv, sync_season (map first),
  harvest_comment_argv, close_issue_argv; the s78 dry-run proved the
  render on the live board
- w1 lands the issue #2 fix + tests/test_s79_w1_pins.py; the close's
  board --map s79 wires the lanes to issue #2
- lint.py resolves `ledger:<id>@<sha>` citations — the surface issue
  #2 says append_record diverges from

## Task (spec-first, pins in tests/test_s79_w2_pins.py, _s79w2_ prefix)
1. Pin sync_season over a fixture campaign whose map names issue #2
   and whose harvest record exists: the dry-run render carries the
   issue url, the sealed record's verbatim body, and writes nothing.
2. Pin the full-loop composition: emit_lane_map + issue_for_season +
   sync dry-run chained in one test — the s78 helpers compose, no
   re-derivation.
3. Pin lint's resolver against the citation forms append_record emits
   (the pre-fix form is the red-shaped contract; w1's fix makes the
   emitted form resolve — your pin holds whichever form the merged
   tree emits, asserting resolution succeeds).
4. notes.md REQUIRED: the pin map, what stayed with w1.

## Bounds
- Edits: src/rumpun/board.py (composition only), tests/. No lint.py
  edits (w1's lane owns the fix side). No live gh call in pins.
