# s80 w1 — triage issues #3 and #4: stale or real (the audit's residuals)

The board-pulled loop now works. Your lane: take the two factual
residuals, measure them against today's tree, and resolve each either
way — fix, or close-with-evidence.

## Ground truth (measured 2026-09-17)
- issue #3: "Independent artifact checks remain absent (audit-43
  residual)" — the residual's text is from usefulness-decade-1, an
  OLD audit era; independent checks have existed since s55 and grew
  through s63/s65/s67
- issue #4: "Ledger shows 24 WIN, 8 LOSS, 2 missing, not 34 completed
  improvements" — the auditor counted a different window or slot set;
  the s64 counts-honesty contract is on the tree
- the loop: board --map s80 <issue url> per issue at close; sync
  closes with the sealed evidence

## Task
1. For each issue: measure the claim against TODAY's tree. #3: does
   an absent-path check exist (name it, run it, record rc)? #4: run
   the counts composer fresh and reconcile its slots against the
   auditor's numbers (where did 24/8/2 come from — a stale window?).
2. Resolve each: if stale, comment the evidence (the check's name +
   its passing run / the composer's fresh output) and close it
   through the argv builders (no sync needed — single-issue lanes).
   If real, file the precise gap as a NEW issue (a child of the
   residual) and close the parent pointing at the child.
3. board --map s80 per resolved issue url; notes.md REQUIRED: the
   measurement, the resolution, the issue urls.

## Bounds
- Read-only on the tree except notes. One measurement pass per issue.
  Honest resolutions only: a stale residual closes on evidence; a
  real one stays open as a child with the fix scoped.
