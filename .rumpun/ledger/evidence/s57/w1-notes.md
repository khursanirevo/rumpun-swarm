# s57 w1 — the check rides every close

## Shipped
- src/rumpun/cli.py: cmd_harvest runs the close check. After
  harvest_season writes the akar record AND the verdicts.jsonl verdict
  row, _run_check (the cmd_check path, extracted verbatim into one
  helper both call) runs the checker subprocess once with sid + the
  repo HEAD; the check-<sid> record lands in the default ledger dir
  beside the harvest record.
- Honesty protocol (documented in the module docstring and the
  cmd_harvest docstring): a check DELTA or structural refusal never
  suppresses or rewrites the verdict row or the harvest record; the
  outcome is logged ("check <sid> at close: exit N (recorded; the
  verdict row stands)"), and the close exits on the harvest alone (0)
  unless --strict passes the check exit through (0 VERIFIED / 1 DELTA /
  2 structural refusal). New harvest --strict flag. Additive: the check
  verb is behavior-identical (same subprocess, exits, record placement).

## Verification (measured this session, 2026-09-16)
- Fixture campaign: git clone of the repo at 8bba847 per case; s56
  state planted (runs/s56/_season/state.json, status completed); the
  pre-harvest ledger restored (s56-harvest record removed from the
  working tree, verdicts.jsonl emptied). Runs use the workspace scratch
  src (probe: import resolves to w1/scratch/src/rumpun/cli.py) and the
  repo venv python.
- fix1 honest close `harvest s56 --verdict WIN --implies x`: exit 0;
  BOTH records side by side in .rumpun/ledger (2026-09-16_s56-harvest.md
  + 2026-09-16_check-s56.md); verdict row intact (verdict WIN, implies
  x); check verdict DELTA -- sole delta "pins not green in the extracted
  tree (exit 1)": the s56 honest-close pin needs .git inside the
  extracted tree for its own recursive check, which git archive never
  carries; pre-existing property of the s56 pins in extracted contexts,
  not a regression of this change. Seal recomputed MATCH (eceef15d...),
  every ships clause MATCH.
  Bare-tree re-run names the failing pin exactly: test_s56w2_check_verb_honest_close_s54_verifies (git rev-parse "not a git repository" inside the extracted tree); log in evidence/bare-pins.log.
- fix2 forced DELTA (failing pin appended to the committed tree): exit
  0 non-strict; the DELTA record names the deltas ("pins not green";
  "claims 4 pins, tree carries 5"); verdict row byte-identical to
  fix1's.
- fix3 --strict on the same fixture: exit 1 (check exit passes
  through); DELTA record and row intact.
- fix4 structural refusal (s56 ships row removed from DESIGN.md):
  exit 0 non-strict; NO check record (the checker refuses before its
  record write); the log names the cause ("no ships row for s56"); row
  intact.
- py_compile OK; ruff clean (exit 0, --no-respect-gitignore).
- Suite floor: 252/253 in 267.68s; the only red is the s38 coldstart pin, and it
  fails solo too (98.12s) -- but the traceback names the cause: the pin
  hashes the whole .rumpun tree across one checker run, and five paths
  changed under it, all live worker-session files (runs/s57/w1 and w2
  agent.log + state.json, w2 .omc throttle state) of the two RUNNING
  workers, one of them this session itself. The checker passed 11/11 in
  its temp dir; nothing under src/, ledger/, seasons/, prompts/ moved;
  my cli.py change touches none of the five paths. The pin is
  structurally red while s57 workers are live; green again at close
  (the s56 close ran it green, 253/253). Not a regression.

## Disclosures
- The close-time check targets the repo HEAD, which at harvest time
  predates the season-close commit (the close protocol harvests at step
  3 and commits at step 6). The record pins the resolved sha, so the
  account stays honest. A real VERIFIED at close needs the DESIGN row
  and pins committed first; otherwise the check records DELTA or a
  refusal beside the verdict, per protocol.
- The refusal branch writes no check record (checker refuses before its
  record write); the harvest log is the account there. w2's pin spec 3
  ("refusal exits nonzero") holds for the checker subprocess itself; the
  HARVEST still exits 0 unless --strict, per this brief.
- The workspace src/rumpun/cli.py copy is the merge source; diff-checked
  identical to the live file (DELIVERABLE_IDENTICAL). Scratch fixtures
  live in /tmp/s57w1/ (fix1..fix4), evidence copies in evidence/.
- Live-tree status (this session): beyond src/rumpun/cli.py, the tree
  carries in-flight changes not mine (ledger directives.jsonl, four
  logs/ repro outputs, replay-matrix.md) and untracked harness drafts
  (prompts/dev/w1-epics.md, w2-epic-pins.md, seasons/s58.yaml).
  Untouched; disclosed per the s56 convention.
