# s70 w1 — board completion (the s69 NEUTRAL retry)

The Projects v2 board was blocked on the operator's gh scopes. They may
have refreshed them. Probe first; never fake progress past a blocker.

## Ground truth (measured 2026-09-16)
- repo khursanirevo/rumpun exists (private), main pushed, origin tracking
- seed issue: https://github.com/khursanirevo/rumpun/issues/1
- the blocker was: token missing scopes `project` and `read:project`
- src/rumpun/board.py + kanban seam landed s69; pins 4/4

## Task
1. Probe: `gh project list --owner khursanirevo` (exit 0 = unblocked).
   If it still fails on scopes, STOP: write notes.md saying the NEED
   HUMAN persists, verbatim error included. Do nothing else.
2. If unblocked: `gh project create --title "rumpun" --owner
   khursanirevo`; record the project number.
3. `gh project item-add <number> --owner khursanirevo --url
   https://github.com/khursanirevo/rumpun/issues/1`.
4. Verify live: `gh project item-list --owner khursanirevo --format
   json` parses through rumpun.board.parse_item_list and pickup()
   returns issue #1's row. Fix board.py if the real JSON shape differs
   from the captured fixture (keep the pins' row assertions).
5. Re-run tests/test_s69_w2_pins.py solo; all 4 must stay green.
6. notes.md REQUIRED: project url/number, commands, pickup output.

## Bounds
- No repo changes beyond src/rumpun/board.py; no force-push; no
  .rumpun state edits. One probe, then either the full flow or a stop.
