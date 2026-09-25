# s93 w1 — the board arc extends; the trail stays buried

Maintenance with verification teeth: the arc gains s89-s92, and the
composer's resolution trail is re-verified on fresh data.

## Ground truth (measured 2026-09-17)
- .rumpun/epics.yaml: board-arc carries s69-s88; s89-s92 sit in the
  campaign epic (they closed after the s89 split)
- the s84 composer trail: audit-45 verified buried (the s90 w1 live
  test); the composer reads the resolution trail (the s84 fix)
- issue #16's siblings (#14, #15) have their first slices

## Task
1. Extend the board-arc epic: epics.yaml gains s89-s92 (the arc's
   seasons; the campaign epic keeps the rest). Preserve every verdict
   (the pinned arithmetic rule).
2. Verify the epic view: the two views sum to the whole ledger (the
   pinned invariant); lint passes.
3. Re-run the composer once fresh over the current ledger: audit-45's
   resolved markers stay buried (the s84 contract), any NEW candidate
   lines are recorded in notes.md (not filed — s94 scopes them).
4. notes.md REQUIRED: the epic view output, the arithmetic check, the
   fresh composer lines.

## Bounds
- Edits: .rumpun/epics.yaml only. notes.md REQUIRED. No composer
  edits (verification only).
