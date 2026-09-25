# s28 w2 — DESIGN section 16 + claim-by-claim README verification

You are w2 in season s28 (repo root: the parent of this .rumpun tree). Read
DESIGN.md (sections 13-15 + the season table through s27), README.md (w1 is
rewriting it in the shared lane - read its workspace copy when it lands on
the lane), and the akar records from s17-s27 (codex-review-2026-09-14
through the s27 harvest). You own DESIGN.md; w1 owns README.md. FILE TOOLS
directly. WRITE ONLY inside your workspace. 40 minutes.

## Deliverables

1. DESIGN.md section 16 (workspace copy of the file + notes.md anchors):
   "16) The external-review arc and the corpus gate (s17-s27)" - the arc
   from the 22-finding review through the four fix seasons, the corpus
   gate, the matrix-ingesting audit, and the render tooling, each season
   cited by id with its outcome. Honest counts: 9H/11M/2L landed across
   s17-s24, zero-candidate audits, the two workspace-rule violations, the
   budget retune. Table format matching sections 13-15.
2. README claim verification: for every claim in w1's README workspace
   copy, verify against behavior (run the verb with --help, run the tool,
   check the version). Record claim | verified | evidence in notes.md.
   Zero false claims is w1's band; your record is the proof.

## Constraints

- DESIGN.md patch as a workspace copy + notes.md anchors (harness merges).
- Do not modify src/, tests/, tools/, or cli.py.
- Markdown; table format matching sections 13-15; no marketing language.

## Verify before finishing

Your DESIGN section's season citations match the akar records; your
verification table covers every README claim. notes.md carries both.
