# s39 w1 — honest season counts in the usefulness brief

You are w1 in season s39 (repo root: the parent of this .rumpun tree). Read
tools/usefulness_audit.py (the brief composition + season_count), and akar
records audit-28 + usefulness-decade-3 (the count-honesty residual). FILE
TOOLS directly. WRITE ONLY inside your workspace. 40 minutes.

## Deliverable: the brief reports true counts

Today: season_count(root) counts every musim/s<N>.yaml including drafts
that never ran — the decade-3 review's own residual flagged the inflation.
Fix in the brief composition: two counts reported verbatim to the auditor:
- run seasons: musim yamls whose sid has a rimba state file;
- drafted-only: musim yamls without one.
The headline line carries both (e.g. "3 run, 2 drafted-only, 5 total").
The decade trigger arithmetic (floor(total/10)) is unchanged — the honest
numbers are for the auditor's judgment, not for the debt math.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not modify src/, tests/, or files outside your workspace.
- The 182-test suite stays green.

## Verify before finishing

Repro: a fixture with 3 run + 2 drafted-only seasons produces the both-
numbers headline; the decade debt math is unchanged. Suite green against
patched copies. Both in notes.md.
