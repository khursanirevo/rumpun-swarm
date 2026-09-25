# s93 w2 — issue #16: the completion-effort contract, the last residual

"Repeated harness repairs make autonomous delivery unproven.
Completion effort outside the stopped seasons remains unquantified."
Design what would count, and measure the first slice.

## Ground truth (measured 2026-09-17)
- issue #16 (OPEN, audit-45 residual); siblings #14 and #15 have
  their slices (the board trail; the baseline comparison)
- the harness repairs: the correction commits this campaign carried
  (the check-record DELTA fixes: s62-s90's correction chain) — each
  was a repair the harness performed on its own output
- the honest difficulty: "unproven" is the claim; the quantification
  is repairs-per-season, repair-recurrence, and the effort the
  repairs saved the operator (they never touched them)

## Task
1. Design the completion-effort contract: repairs-per-season (the
   correction commits per close), the recurrence rate (the same
   class re-firing), and the operator-effort counterfactual (the
   repairs the operator never made). Distill into
   priors/templates/completion-effort.md in the kancil-base pack.
2. Measure the first slice from the git log: the correction commits
   (fix:/chore: subjects) per season across the campaign, the
   recurrence count, and the operator's gh commit activity on the
   repo (zero operator commits — the operator never repaired
   anything). The table is the first data point; it proves nothing
   alone, and says so.
3. Comment the contract + the table on issue #16 (one live call,
   disclosed). The issue stays OPEN.
4. notes.md REQUIRED: the design, the table, the comment url.

## Bounds
- Edits: the pack draft dir (one template). One live gh call
  (disclosed). notes.md REQUIRED. No season spawns.
