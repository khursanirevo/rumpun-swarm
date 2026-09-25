# s75 w1 — board create, the write scope is live

Fourth stop's blocker is gone: the operator granted `project` and it is
verified in the token (gh auth status, 2026-09-17). Land the board.

## Ground truth
- repo khursanirevo/rumpun private, main pushed; seed issue #1 filed
- token scopes verified: project + read:org + repo present
- board.py + kanban seam + the s74 lifecycle all landed; 10+4 pins green
- item-list quirk (w1 s74 diagnostic): non-interactive item-list needs
  the board number — pass it once the create returns it

## Task
1. Probe: `gh auth status` shows `project` (rc=0 confirmation only).
2. `gh project create --title "rumpun" --owner khursanirevo`; record
   number + url.
3. `gh project item-add <number> --owner khursanirevo --url
   https://github.com/khursanirevo/rumpun/issues/1`.
4. Verify live: `gh project item-list --owner khursanirevo <number>
   --format json` (with the number) parses through
   rumpun.board.parse_item_list; pickup() returns issue #1's row.
   Fix board.py's argv only if the real shape needs the number.
5. Re-run tests/test_s69_w2_pins.py and tests/test_s74_w2_pins.py
   solo; all green.
6. notes.md REQUIRED: number, url, commands, pickup output.

## Bounds
- board.py only if the argv shape demands it. One probe, then the
  flow or an honest stop. No force-push, no .rumpun state edits.
