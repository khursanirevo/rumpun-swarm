# s56 w1 — the check verb, wired

You are w1 in season s56 (repo root: the parent of this .rumpun tree).
Read tools/artifact_check.py (the landed checker, s55), src/rumpun/cli.py
(the plugin verb wiring precedent), and ledger records s55's harvest +
audit-39. FILE TOOLS directly. WRITE ONLY inside your workspace EXCEPT
minimal documented cli.py + audit.py changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. cli.py gains the check verb: `rumpun check <sid> <close-commit>
   [--out-dir DIR]` - argparse wiring onto the checker's run (module
   import or subprocess of tools/artifact_check.py; the record lands in
   the default ledger dir unless --out-dir redirects).
2. audit.py: the F1 phase-liveness comment (the "existence at
   rimba/<sid>/" block, ~line 547) names the real runs path
   (.rumpun/runs/<sid>/ via paths.runs_dir). Comment-only; no behavior.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- Additive: the suite floor holds; the known race flakes stay the only reds.

## Verify before finishing
`rumpun check s54 614aabf5a4a017e84b08caa60c57f7098afdc627 --out-dir
/tmp/check-verb` exits 0 with VERIFIED. Suite floor. All in notes.md.
