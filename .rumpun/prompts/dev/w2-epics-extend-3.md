# s98 w2 — the board arc extends with s97; the arithmetic holds on the extended epic

Maintenance pinned twice: the board arc gains s97, and the extended
epic's arithmetic holds (the s89 contract, w1's s97 pins' neighbor).

## Ground truth (measured 2026-09-18)
- .rumpun/epics.yaml: board-arc carries s69-s96; s97 sits in the
  campaign epic (it closed after the s96 extension)
- the pinned arithmetic: the two views sum to the whole ledger (the
  s89 w2 contract, w1's s97 neighbor pins)
- the board: #5 OPEN by design, #11/#12 OPEN operator-side, #14-#16
  OPEN with slices, everything else closed with evidence

## Task
1. Extend the board-arc epic: epics.yaml gains s97. Preserve every
   verdict (the pinned arithmetic).
2. Verify the epic view: the two views sum to the whole ledger; lint
   passes.
3. notes.md REQUIRED: the epic view output, the arithmetic check.

## Bounds
- Edits: .rumpun/epics.yaml only. notes.md REQUIRED. No other tree
  edits.
