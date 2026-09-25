# s74 w1 — board completion, the scope is live

Four honest stops are behind you. The blocker is GONE: verified
2026-09-17 post-s73 with a clean no-pipe probe (`gh project list
--owner khursanirevo` rc=0, empty list). Complete the board this time.

## Ground truth
- repo khursanirevo/rumpun private, main pushed; seed issue #1 filed
- read:project scope CONFIRMED live (rc=0 probe, 2026-09-17)
- board.py + kanban seam landed; 4 board pins + 8 panel pins green

## Task
1. Re-probe to confirm from your own session (rc=0 expected).
2. `gh project create --title "rumpun" --owner khursanirevo`; record
   the project number and url.
3. `gh project item-add <number> --owner khursanirevo --url
   https://github.com/khursanirevo/rumpun/issues/1`.
4. Verify live: `gh project item-list --owner khursanirevo --format
   json` parses through rumpun.board.parse_item_list; pickup() returns
   issue #1's row. Fix board.py only if the real JSON shape differs
   (keep the pins' row assertions).
5. Re-run tests/test_s69_w2_pins.py solo; all 4 stay green.
6. notes.md REQUIRED: project url/number, every command, the pickup
   output, and the real item-list JSON shape you saw.

## Bounds
- board.py only if the shape differs. No force-push, no .rumpun state
  edits. If anything blocks, one probe, then an honest stop as ever.
