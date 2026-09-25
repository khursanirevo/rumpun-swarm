# s57 w1 — the check rides every close

You are w1 in season s57 (repo root: the parent of this .rumpun tree).
Read src/rumpun/cli.py (cmd_harvest, cmd_check), tools/artifact_check.py
(the checker), and ledger records s56-harvest + audit-40. FILE TOOLS
directly. WRITE ONLY inside your workspace EXCEPT minimal documented
cli.py changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. cmd_harvest runs the check after writing the verdict row: the
   checker subprocess (the cmd_check path) with sid and the repo HEAD,
   the check-<sid> record landing in the default ledger dir.
2. The honesty path: a check DELTA (or a structural refusal) never
   suppresses or rewrites the verdict row - the harvest logs the check
   outcome, the check record sits beside the harvest record, and the
   exit code reflects the harvest (not the check) unless --strict.
   Document the protocol in the cli docstring.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- Additive: the suite floor holds; the known race flakes stay the only reds.

## Verify before finishing
`rumpun harvest s56 ... --verdict WIN --implies x` in a copied fixture
campaign writes both records. Suite floor. All in notes.md.
