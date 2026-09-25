# s71 w1 — board completion, second retry

The blocker narrowed at s70: only the `read:project` scope is missing
(`project` landed). Probe once; the honest stop stays the contract.

## Ground truth (measured 2026-09-17)
- repo khursanirevo/rumpun private, main pushed; seed issue #1 filed
- s70 probe: `gh project list --owner khursanirevo` exit 1, error named
  [read:project] only
- board.py + kanban seam landed; pins 4/4 (s69) + 5/5 panel pins (s70)

## Task
1. Probe: `gh project list --owner khursanirevo`. Still scope-blocked?
   STOP: notes.md with the verbatim error, nothing else runs.
2. Unblocked: `gh project create --title "rumpun" --owner khursanirevo`
   (record the number), `gh project item-add <number> --owner
   khursanirevo --url https://github.com/khursanirevo/rumpun/issues/1`.
3. Verify live: `gh project item-list --owner khursanirevo --format
   json` parses through rumpun.board.parse_item_list; pickup() returns
   issue #1's row. Fix board.py only if the real JSON shape differs
   (keep the pins' row assertions).
4. Re-run tests/test_s69_w2_pins.py solo; all 4 stay green.
5. notes.md REQUIRED: project url/number, commands, pickup output.

## Bounds
- One probe, then either the full flow or an honest stop. No
  force-push, no .rumpun state edits, board.py only if shape differs.
