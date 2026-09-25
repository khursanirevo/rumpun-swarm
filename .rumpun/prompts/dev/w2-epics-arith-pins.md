# s89 w2 — pin the epic rollup's arithmetic (the s85 split as the contract)

The board-arc split preserved every verdict (11/0/5 + 57/9/2 = 68/9/7)
and w1 extends the arc with s85-s88 now. Your slice: the arithmetic
becomes a pinned contract — the views always sum to the whole.

## Ground truth (measured 2026-09-17)
- epics.py: the rollup reads runs/<sid>/verdicts.jsonl + the persisted
  state contract; the s85 split verified by hand (the w1 notes)
- the s85 render: `board-arc s69-s84 11 WIN / 0 LOSS / 5 other` +
  `campaign s1-s85 57 WIN / 9 LOSS / 2 other`
- no verdict may appear twice or vanish (the no-double-membership lint
  exists; the arithmetic pin does not)

## Task (spec-first, pins in tests/test_s89_w2_pins.py, _s89w2_ prefix)
1. Pin the sum invariant over fixture epics: board-arc's verdict
   counts + campaign's counts == the whole-ledger counts (the s64
   composer convention), for every fixture permutation (a season
   moving between epics preserves the sum).
2. Pin the no-double-membership + no-vanish pair: a season in two
   epics is a lint error; a season in no epic is marked (the s85
   `(no state: s1)` shape).
3. Pin the extension behavior: adding s85-s88 to board-arc (w1's
   landing) keeps the sum (fixture: the pre-extension and
   post-extension docs both sum to the same total).
4. notes.md REQUIRED: the pin map.

## Bounds
- Edits: tests/ only. No live gh call. notes.md REQUIRED.
