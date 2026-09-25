# s92 w2 — issue #15: the baseline comparison, designed honestly

"No baseline comparison establishes that the season loop improves
delivery speed, quality, or cost over ordinary development." The
deepest open question. You cannot prove it in a season; you can
design what would count, and measure the first honest slice.

## Ground truth (measured 2026-09-17)
- issue #15 (OPEN, audit-45 residual); #14 is its sibling (filed)
- the campaign's own history is the data: 92 seasons, the verdict
  histogram, the repair record (issues #2/#6/#10/#13/#17 were real
  defects the loop found, filed, and fixed through itself)
- the honest difficulty: "ordinary development" has no baseline on
  this box; the operator's manual kancil competition work is the
  closest thing to a parallel effort

## Task
1. Design the baseline-comparison contract: what a fair comparison
   measures (time-to-fix a filed defect: board-pulled seasons vs the
   operator's manual turnaround on exp_manager issues; defect escape
   rate: the check records' DELTA catches vs the escapes; the repair
   recurrence rate: do fixed defects stay fixed). Distill into
   priors/templates/baseline-comparison.md in the kancil-base pack.
2. Measure the FIRST honest slice from the ledger: the five board
   defects (#2, #6, #10, #13, #17) — filed-to-closed elapsed time,
   each fixed through the loop, zero recurrences to date. The table
   is the first data point; it proves nothing alone, and says so.
3. Comment the design + the table on issue #15 (one live call,
   disclosed). The issue stays OPEN (a first slice closes nothing).
4. notes.md REQUIRED: the design, the table, the comment url.

## Bounds
- Edits: the pack draft dir (one template). One live gh call
  (disclosed). notes.md REQUIRED. No season spawns.
