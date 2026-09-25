# s57 w2 — spec-first pins for the harvest-integrated check: notes (2026-09-16)

Spec anchors: the season goal (seasons/s57.yaml: "the verdict row and the
check record land together, so a season's WIN never rests only on its own
workers' reports"), w1's brief (.rumpun/prompts/dev/w1-harvest-check.md),
ledger records 2026-09-16_s56-harvest and 2026-09-16_audit-39/40 (the
usefulness residual the ride-along check closes). Precedent file:
tests/test_s56_w2_pins.py (fixture + subprocess + bounded-run shape).

## Deliverable

.rumpun/runs/s57/w2/tests/test_s57_w2_pins.py — 4 pins, additions-only,
`_s57w2_` helpers, py3.10+, ruff clean at line-length 100, no prints,
no rumpun imports (subprocess and file reads only). Graft: land this file
in repo tests/ as-is.

- pin 1  test_s57w2_harvest_lands_row_and_check_record        (spec 1)
- pin 2  test_s57w2_delta_check_does_not_rewrite_the_verdict  (spec 2)
- pin 3a test_s57w2_structural_refusal_exits_nonzero          (spec 3)
- pin 3b test_s57w2_harvest_record_byte_stable_across_runs    (spec 3)

## Interface contract the pins hold

`rumpun harvest <sid> --verdict V --implies X` runs the artifact check
(the cmd_check path: the checker at <project-root>/tools/artifact_check.py
as an isolated subprocess, sid and the repo HEAD) AFTER the record and
verdict row land; the check-<sid> record goes to the default ledger dir.
Honesty protocol (w1's brief): a check DELTA or structural refusal never
suppresses or rewrites the verdict row or harvest record; the exit
reflects the harvest alone (0) unless --strict passes the check exit
through (0 VERIFIED / 1 DELTA / 2 structural refusal). Every harvest run
is a subprocess bounded by S57W2_TIMEOUT (the spec's 240s bound; measured
runs: 1.3–3.0s).

Fixture (check-compatible miniature campaign, built per pin under
pytest tmp_path): DESIGN.md with a true ships row (file claim only — no
key/slash/pins/suite claims to trip the ships analyzer), src/rumpun/
__init__.py, committed pins that pass in the extracted tree, a copy of
tools/artifact_check.py (cmd_check resolves the checker from the project
root), .rumpun/{rumpun.yaml,runs,ledger}, terminal state.json with fixed
timestamps (deterministic record), git init + commit; the commit content
is read back via git ls-files so a lost file fails at build time. Pin 2
tamper: rewrite the ships row to claim a missing file, commit (HEAD =
tampered tree, which is what the checker extracts).

## Measured red set

Two snapshots, both measured (w1 landed cmd_harvest + _run_check +
--strict in the shared tree UNCOMMITTED mid-flight: `M src/rumpun/cli.py`
+79/−15 vs HEAD when last checked).

Snapshot P — pristine clone of HEAD 8bba847 (`git clone`, not archive:
the tarball extract has no .git and 15 pins red for the wrong reason;
clone has real git history, PYTHONPATH=clone/src, resolution probed:
rumpun resolves to clone/src): **3 failed, 1 passed in 1.30s**.

| pin | clause | outcome | measured reason (pristine) |
|---|---|---|---|
| 1 both records | spec 1 | RED | harvest record lands, no check record: "no record carrying 'id: check-fx01'"; ledger listing shows only fx01-harvest |
| 2 DELTA honesty | spec 2 | RED | same shape for fx03: harvest record present, no check record to carry DELTA |
| 3a refusal | spec 3 | RED | rc nonzero only via argparse: "unrecognized arguments: --strict"; nothing names fx02 — the close runs no check, so no refusal exists to surface |
| 3b byte-stable | spec 3 | GREEN | the pristine record is already deterministic; this pin holds the merge (no clocks or check output in the harvest record), documented in its docstring |

Snapshot L — the live tree with w1's uncommitted landing: **4 passed in
3.04s** (PYTHONPATH=src, repo venv, file run from the workspace
pre-graft).

## Honest-close evidence (measured, not projected)

A preserved pin-1 run (--basetemp=/tmp/s57w2_demo) shows the full chain
against the fixture repo: check-fx01 record "independent artifact check
fx01 @ 67677ef66d59 (VERIFIED)", git -C <fixture> rev-parse/archive (6
files), fixture pins "exit 0; 2 passed; ... 0.2s; probe resolved
.../tree/src/rumpun/__init__.py", packs/seals notes, verdict: VERIFIED;
verdicts.jsonl row: fx01 WIN with the operator's implies. Both records in
.rumpun/ledger/ of the fixture.

## Merge gate (measured)

- Baseline, pristine clone, no pins file: **11 failed, 240 passed,
  2 skipped in 107.80s** (/tmp/s57w2_baseline.log).
- Same clone with the pins file added: **14 failed, 241 passed,
  2 skipped in 92.84s** (/tmp/s57w2_full.log). Delta over baseline is
  exactly my file: pins 1, 2, 3a red for the spec reasons above, 3b
  green. Floor holds: my file adds no red beyond its own spec reds.
- The 11 baseline reds are clone-environment reds, identical in both
  runs: test_rumpun.py's repo-root helper refuses the clone ("repo root
  not found above /tmp/s57w2_red_base/tests/test_rumpun.py"), taking the
  4 render_dashboard and 7 coldstart pins with it. The helper's exact
  criterion is not root-caused here; it does not affect the delta.
- The live-tree full suite was deliberately NOT run: src/ carries w1's
  uncommitted edits mid-flight, and a full-suite baseline races the
  sibling worker's src/ edits (the s56 w2 precedent ran its live baseline
  only while src/ was clean). Floor certification rests on the
  same-clone delta above plus the live solo run (4 passed).
- ruff: `~/.local/bin/ruff check --no-respect-gitignore --line-length
  100` on the pins file -> All checks passed.
- Interpreter: repo .venv python (3.13), pytest 9.1.1; PYTHONPATH pinned
  to the tree under test ahead of the editable install (probed).
- No transient copy remains in repo tests/ (s57 file count 0, read back).

## Logs (all outside the repo)

/tmp/s57w2_solo.log (live-tree pins, 4 passed), /tmp/s57w2_demo.log and
/tmp/s57w2_demo/.../fx/.rumpun/ledger/ (preserved honest-close records),
/tmp/s57w2_baseline.log (clone baseline), /tmp/s57w2_solo_pristine.log
(pristine red set), /tmp/s57w2_full.log (clone suite with pins added),
/tmp/s57w2_probe.py (import-resolution probe).
