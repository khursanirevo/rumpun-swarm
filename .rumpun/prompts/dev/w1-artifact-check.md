# s55 w1 — the independent artifact check

You are w1 in season s55 (repo root: the parent of this .rumpun tree).
Read src/rumpun/plugin.py (priors_digest), tools/replay_corpus.py (the
isolated-runner precedent), DESIGN.md sections 13-16, ledger records
s54-harvest + audit-39 (the residuals this lands). FILE TOOLS directly.
WRITE ONLY inside your workspace EXCEPT minimal documented tools/ +
cli.py changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. tools/artifact_check.py: `python tools/artifact_check.py <sid>
   <close-commit>` re-verifies the named season's landed ships from
   artifacts alone: extract the close commit to a temp tree (git
   archive), run the season's merged pins there (repo venv, PYTHONPATH
   from that tree), recompute any claimed pack digests, and diff the
   DESIGN ships row against the tree (each named ship: file exists and
   carries the named surface).
2. The check writes a ledger record (check-<sid>): the commands run, the
   pins outcome in the extracted tree, the digest comparisons, the
   ships-row diff (each row: MATCH or the named delta), and an honest
   verdict line VERIFIED or DELTA.
3. cli wiring (minimal, documented): `rumpun check <sid> <close-commit>`.

## Constraints
- Git ops via subprocess git; git archive only - no checkout, the live
  tree is never touched.
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).

## Verify before finishing
Run the checker on s54's close commit: VERIFIED with the pins green in
the extracted tree and the ships rows matching. Suite floor. notes.md.
