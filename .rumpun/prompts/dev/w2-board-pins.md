# s69 w2 — pins for the board lane (directive seq 6 discipline, seq 14 surface)

Pin the board lane's offline-verifiable contract. Live gh calls stay in
w1's lane; your pins must pass without network flakiness.

## Ground truth
- s68-harvest (see ledger): forge flow landed; schema versioning live
  (schema: 1 + CHANGELOG refusal path, s68 pins).
- s69 w1 creates: khursanirevo/rumpun (private), a Projects v2 board,
  one seed issue on the board.

## Task (spec-first, pins in tests/test_s69_w2_pins.py, _s69w2_ prefix)
1. Pin: the board pickup module (src/rumpun/board.py, w1 lands it with
   the brief) parses `gh project item-list --owner khursanirevo
   --format json` output - pin the PARSER against a captured JSON
   fixture string (open/closed items, titles, urls), no gh call.
2. Pin: the filing command construction - the module builds the exact
   `gh issue create`/`gh project item-add` argv from a (title, body)
   pair; pin argv equality.
3. Pin: `git -C <repo> remote get-url origin` names khursanirevo/rumpun
   (the one live check; skip nothing - if the remote is missing the pin
   REDS for the spec reason and w1's landing is incomplete).
4. Pin: kanban's NEED HUMAN still renders when the board module raises
   (the board degrades to the local columns; no crash).

## Bounds
- 40-60 min budget. No edits outside src/rumpun/board.py + tests/.
- notes.md REQUIRED (s68 shipped none).
