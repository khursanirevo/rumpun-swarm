# s96 w2 — the spend lines render on the grown ledger; issue #18 gets its rule

The spend line landed in s95 and rendered once. Your lane: render it
over the grown ledger (s94-s95's harvests now exist), then apply the
cost template's stay-open rule to issue #18 — the rule decides the
issue's fate, not hope.

## Ground truth (measured 2026-09-18)
- the composer (tools/usefulness_audit.py): harvest_spend + the
  spend lines landed s95 (the writer-seconds sums, the pre-writer-table
  exclusions by name, the corrupt-cell refusals); the label split
  renders live
- s94/s95's harvest records exist with per-writer tables — the grown
  ledger's new spend lines
- priors/templates/cost-accounting.md: the stay-open closing rule
  (what keeps #18 open: the unrecordables remain unrecordable)

## Task
1. Run the composer fresh over the current ledger: the spend lines
   cover s94/s95's harvests, the label split renders, plain records
   byte-stable. notes.md carries the render.
2. Read the cost template's stay-open rule and apply it to issue #18:
   comment the landed spend-line evidence (the s95 render + the grown
   ledger's lines, citing the sealed s95-harvest record) and follow
   the rule's verdict — stay open (the unrecordables remain) or close
   (only if the rule says the contract is fully delivered).
3. notes.md REQUIRED: the render, the rule's verdict, the comment url.

## Bounds
- One live gh call (the comment; a close only if the rule says so).
  No composer edits (render + verify only). notes.md REQUIRED. No
  .rumpun state edits.
