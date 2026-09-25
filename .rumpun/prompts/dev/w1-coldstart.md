# s37 w1 — tools/coldstart_check.py (the external-task verification)

You are w1 in season s37 (repo root: the parent of this .rumpun tree). Read
README.md (the quickstart you are verifying), src/rumpun/cli.py (the verb
surface), tools/render_dashboard.py (the tooling pattern), and akar records
audit-26 + usefulness-decade-3 (the external-task-value residual). FILE
TOOLS directly. WRITE ONLY inside your workspace. 40 minutes.

## Deliverable: tools/coldstart_check.py (workspace copy)

An isolated end-to-end verification of the documented quickstart, in a
temp dir, against a stub model route (no network, no fable):
1. rumpun init <dir> — the scaffold exists (rumpun.yaml, musim/, prompts/,
   akar/, rimba/).
2. The scaffolded season edited minimally in-process: stub model route
   (a script writing a results row), benih names set.
3. rumpun lint passes on the edited season.
4. rumpun season start runs the season to completed (stub route exits 0
   writing results.jsonl).
5. rumpun harvest marks the verdict and writes the season row.
6. rumpun audit runs and lands its record.
Each step: PASS/FAIL logged with its command; exit nonzero on the first
failure; the temp dir survives for inspection (printed at the end).
No campaign state touched: the check runs entirely in its temp dir.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not modify src/, tests/, or any file outside your workspace.
- The 175-test suite stays green.

## Verify before finishing

Run the checker: every step PASS, exit 0, temp dir printed with the
artifacts in place. Suite green (175). Both in notes.md.
