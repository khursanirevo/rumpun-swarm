# s56 w1 — the check verb, wired

## Shipped
- src/rumpun/cli.py: new `check <sid> <close-commit> [--out-dir DIR]` verb.
  cmd_check runs tools/artifact_check.py as an isolated subprocess under the
  repo venv python (else sys.executable), re-logs the checker's stderr, and
  passes the verdict exit through (0 VERIFIED / 1 DELTA / 2 structural
  refusal), hard cap CHECK_TIMEOUT_S = 600s. Without --out-dir the record
  lands in the checker's default (repo .rumpun/ledger). Module docstring
  names the verb.
- src/rumpun/audit.py: F1 phase-liveness comment only; "rimba/<sid>/" now
  names the real path ".rumpun/runs/<sid>/ via paths.runs_dir". No behavior
  change (2 comment lines -> 3).
- Deliverable copies: src/rumpun/cli.py and src/rumpun/audit.py in this
  workspace, diff-checked identical to the live files. The live edit is the
  prompt-permitted documented exception; the copies are the merge source.

## Verification (all measured this session, 2026-09-16)
- py_compile both files OK; `import rumpun` resolves to live
  /mnt/data/work/rumpun/src/rumpun/__init__.py.
- ruff 0.14.10 --no-respect-gitignore on both files: clean, exit 0.
- .venv/bin/rumpun check s54 614aabf5a4a017e84b08caa60c57f7098afdc627
  --out-dir /tmp/check-verb: exit 0, verdict VERIFIED; record copied here
  as 2026-09-16_check-s54.md (pins 8/8 green in the extracted tree, s54
  harvest seal recomputed MATCH, every ships clause MATCH).
- rumpun check --help: exit 0; missing args: exit 2 (argparse usage).
- Suite floor: PENDING (log /tmp/w1-suite-floor.log).

## Disclosures
- The default-ledger branch (no --out-dir) is the s55 checker's own default
  (repo/.rumpun/ledger); not run live — running it would append a campaign
  ledger record outside this task's write scope. The redirect path is what
  was exercised.
- The live tree carried unrelated in-flight changes from the sibling lane
  (logs/s18..s22 repro outputs, replay-matrix.md); untouched, not mine.
- Edit blocks moved to /tmp/w1-blocks; the workspace holds deliverables and
  harness bookkeeping only.
