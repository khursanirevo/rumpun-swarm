# s42 w2 — independent verification of the decade-4 audit

You are w2 in season s42 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-16, akar records audit-31 + usefulness-decade-3 (the
prior decade's residuals and their closure state). FILE TOOLS directly.
WRITE ONLY inside your workspace. 40 minutes.

## Deliverable: independent verification (notes.md)

1. Re-run the decade contract checks against the REAL ledger: the
   usefulness-decade-4 record exists with a parsed verdict and an
   evidence pointer; the F7 finding retires (a fresh audit run no longer
   reports decade 4 due — verify via tools/replay_corpus.py's sibling:
   run `uv run rumpun audit --corpus` in a SCRATCH copy, never on the
   real ledger).
2. Sample verification: pick three of w1's triage verdicts and verify
   each against source yourself (confirmed means the cited file:line
   shows the claim).
3. Closure ledger: for usefulness-decade-3's residuals, the season or
   record that closed each, or OPEN.

## Constraints

- Do not modify src/, tools/, or files outside your workspace.
- Never echo route output beyond verdict/residual lines; never token
  values.
- The 171-test suite stays green (this season changes no code).

## Verify before finishing

Your verification table covers the decade contract plus three triage
samples, each with your own evidence. In notes.md.
