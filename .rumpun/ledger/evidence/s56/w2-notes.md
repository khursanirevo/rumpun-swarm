# s56 w2 — spec-first pins for the check verb: notes (2026-09-16)

Spec anchors: the season goal (seasons/s56.yaml: "the check verb wired into
the cli plus the last rimba string (the audit F1 comment)"), w1's brief
(.rumpun/prompts/dev/w1-check-verb.md), ledger records 2026-09-16_s55-harvest
("the check verb wiring is the disclosed residual") and 2026-09-16_audit-39
(the usefulness residual the checker closes). Precedent files:
tests/test_s55_w2_pins.py (checker subprocess shape), tests/test_s54_w2_rename_pins.py
(grep sweep shape), tools/artifact_check.py (the s55 checker these pins wire).

## Deliverable

.rumpun/runs/s56/w2/tests/test_s56_w2_pins.py — 4 pins, additions-only,
`_s56w2_` helpers, py3.10+, ruff clean at line-length 100, no prints,
no rumpun imports (subprocess and file reads only). Graft: land this file
in repo tests/ as-is.

- pin 1  test_s56w2_check_verb_honest_close_s54_verifies   (spec 1)
- pin 2  test_s56w2_audit_comments_name_the_runs_path      (spec 2)
- pin 3a test_s56w2_unresolvable_commit_refuses            (spec 3)
- pin 3b test_s56w2_unknown_sid_refuses                    (spec 3)

## Interface contract the pins hold

`python -m rumpun check <sid> <close-commit> [--out-dir DIR]` — w1's brief
verbatim. cwd inside the repo; the record into DIR when given, else the
project ledger. Every pin redirects --out-dir into tmp_path: no pin writes
the real ledger. Refusals exit nonzero naming what is missing (the sha for
an unresolvable commit, the sid for an unknown season), stderr flowing
through whatever wiring w1 chose. Every verb and tool run is a subprocess
bounded by S56W2_TIMEOUT (the spec's 240s bound).

## Measured red set

w1 landed cli.py + audit.py changes in the shared tree MID-MEASUREMENT
(uncommitted: `M src/rumpun/cli.py` +64 lines with cmd_check, `M src/rumpun/audit.py`
rimba 3 -> 2). Two snapshots, both measured:

Snapshot P — pristine HEAD b0e4662 (git archive extract, pins file copied
into its tests/, repo venv, PYTHONPATH=src): **4 failed in 0.62s**. Every
red is for the spec reason.

| pin | clause | outcome | measured reason (pristine) |
|---|---|---|---|
| 1 honest close | spec 1 | RED | rc 2, no record: argparse "invalid choice: 'check'" — the verb is absent |
| 2 rimba sweep | spec 2 | RED | 3 survivors, all user-visible (lines 5, 169, 551) |
| 3a bad commit | spec 3 | RED | rc 2 passes, naming clause fails: output names 'check', not the sha |
| 3b bad sid | spec 3 | RED | rc 2 passes, naming clause fails: output names 'check', not the sid |

Snapshot L — the live tree with w1's uncommitted landing: **3 passed,
1 failed in 7.81s** (PYTHONPATH=src, repo venv, file run from the
workspace pre-graft).

| pin | outcome | measured reason |
|---|---|---|
| 1 honest close | GREEN | verb rc 0; record carries VERIFIED, no DELTA; direct tool run agrees |
| 2 rimba sweep | RED | 2 survivors remain: module docstring (line 5), _season_running docstring (line 169); w1 fixed the F1 comment (line 551) only |
| 3a bad commit | GREEN | rc nonzero, the sha is named in the streams |
| 3b bad sid | GREEN | rc nonzero, s999 is named in the streams |

## Honest-close evidence (measured, not projected)

A fresh verb run (`rumpun check s54 614aabf5… --out-dir /tmp/s56w2_verbrec`)
exited 0 and wrote 2026-09-16_check-s54.md carrying: id check-s54;
pins "exit 0; 8 passed; collected 8, passed 8, failed 0, errors 0; 2.9s;
probe resolved …/tree/src/rumpun/__init__.py"; the ships row "| 8 pins |
MATCH | pins claim 8 == collected 8 |"; verdict: VERIFIED.

## Merge gate (measured)

- Baseline, no pins file (HEAD b0e4662, src/ clean at launch): **248 passed,
  1 failed in 120.14s** (/tmp/s56w2_baseline.log, exit 1) — the s38
  coldstart race the only red.
- With the pins file added: **251 passed, 2 failed in 124.32s**
  (/tmp/s56w2_full.log, exit 1) — s38 coldstart plus my pin 2 (w1's
  docstring sweep incomplete). The delta over baseline is exactly my file:
  3 green verb pins, 1 red for the spec reason. Floor holds.
- The transient tests/ copy was removed after measurement (no s56 file in
  repo tests/; count 0, read back).
- Race flakes: s38 coldstart red in both runs. The brief's "two known race
  flakes": only this one appeared in any of my runs; I did not observe a
  second.
- ruff: `~/.local/bin/ruff check --no-respect-gitignore --line-length 100`
  on the pins file -> All checks passed.
- Interpreter: repo .venv python 3.13.12, pytest 9.1.1, PYTHONPATH=src.
- Tree state at measurement: src/ carried w1's uncommitted cli.py/audit.py
  edits (rimba count 2 when last checked). If w1's final landing sweeps
  lines 5 and 169 too, pin 2 goes green at merge; if their brief's narrower
  scope (F1 comment only) is what lands, pin 2 stays red and the harness
  reconciliation should either extend the sweep or narrow the pin.

## Logs (all outside the repo)

/tmp/s56w2_baseline.log (baseline suite), /tmp/s56w2_solo.log (live-tree
pins run), /tmp/s56w2_solo_pristine.log (pristine-HEAD pins run,
/tmp/s56w2_red_base extract), /tmp/s56w2_full.log (suite with pins added),
/tmp/s56w2_verbrec.log and /tmp/s56w2_verbrec/2026-09-16_check-s54.md
(the verb's honest-close record).
