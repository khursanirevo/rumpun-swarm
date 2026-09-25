# s25 w2 — matrix break fixes + regression pin

Scope: fix src/tests for anything w1's replay matrix marks REGRESSED on
main; record DRIFT honestly; ship one pin test that runs the runner and
asserts no REGRESSION verdicts (SKIP allowed where w1 marks it).
Baseline commit: c973651 (s24 win closes backlog; s25 seeded).

## Baseline on main (w2-verified, pre-matrix)

- Suite: `python -m pytest tests/ -q` -> **123 passed**, 31.11s, exit 0.
  Evidence: scratch/baseline-suite.txt
- Contract greps: report.py renders from read_persisted_status with footer
  `state sha256:<12hex> [H]` (src/rumpun/report.py:595,658); cli.py maps
  single-season verb exits through engine.status_exit_code
  (src/rumpun/cli.py:202); engine.py carries H2 identity check, H5
  validate-then-spawn + pid-None intents, H9 per-agent budgets, M1
  read_persisted_status, M5 status_exit_code + finalize downgrade,
  s17 transition-gated file-tools WARNING, s24 content-based stall.

## w2 pre-matrix runs (all six scripts vs main src)

Ran the corpus myself before w1's matrix landed; protocol v2: lane events
refine, never gate. Raw output files live in scratch/ (exit codes captured,
never hand-transcribed).

| script | w2 verdict vs main | evidence |
|---|---|---|
| s18 w1-warn-repro.py (PYTHONPATH=src) | PASS exit 0 (1 WARNING, 1 lane event, sticky mark, offset 419/419) | scratch/s18-warn.txt |
| s18 w1-h6-loop.py (hardcoded repo src) | exit 0, both-appends 0 of 20 (append lock serializes) | scratch/s18-h6.txt |
| s19 w1-repro-h2-h3.py (main src copied beside script) | PASS exit 0 (H2=PASS H3=PASS) | scratch/s19-h2h3.txt |
| s20 w1-repro.py src | PASS exit 0, 13/13 checks | scratch/s20-h5h9.txt |
| s22 w1-repro-m1.py . | GREEN exit 0, 4/4 checks | scratch/s22-m1.txt |
| s22 w1-repro-m5.py . | GREEN exit 0, 23/23 checks | scratch/s22-m5.txt |

No REGRESSION candidate found by w2's own runs at c973651. The matrix is
the authority; if it disagrees, w2 reproduces with the runner's exact
adapter before touching main.

## Matrix verdicts (w1 authoritative) — filled when replay-matrix.md lands

pending

## REGRESSION fixes

pending

## DRIFT records

pending

## Regression pin

pending
## Regression pin (drafted and proven on synthetic matrices)

Location: tests/test_rumpun.py append (workspace copy
tests/test_rumpun.py, byte-identical to main's plus the s25 pin append).
Two parts:

- `_replay_matrix_rows(repo)` — runs tools/replay_corpus.py (subprocess,
  cwd=repo, timeout 900s), locates replay-matrix.md (tools/ first, then
  .rumpun/akar/evidence/, then rglob under tools/), parses markdown table
  rows whose second cell is a verdict token {PASS, FAIL, DRIFT, REGRESSION,
  SKIP}; a missing runner or missing/unparseable matrix is a pin FAILURE,
  never a skip (a blocked check is a blocker to report).
- `test_replay_matrix_has_no_regressions()` — asserts zero REGRESSION
  verdicts; SKIP rows allowed per the deliverable; PASS/FAIL/DRIFT rows are
  not pin failures (DRIFT acceptable and honest; plain FAIL is runner
  adaptation debt argued in the matrix note column).

Behavior proofs (replica tree scratch/repl: my patched tests + .rumpun
symlink + main src copy):

- No runner present -> pin FAILS with the missing-runner message
  (scratch/repl/pin-a.txt, exit 1).
- Fake runner emitting a REGRESSION row -> pin FAILS, names the script
  (scratch/repl/pin-b1.txt, 1 failed, exit 1).
- Fake runner emitting all-PASS + one SKIP row -> pin PASSES
  (scratch/repl/pin-b2.txt, 1 passed, exit 0).
- Patched suite without the pin: 123 passed in 31.63s (run from repo root,
  pin deselected) — the append breaks nothing.

## Matrix verdicts (w1 authoritative, replay-matrix.md @ w1 workspace)

Ran 2026-09-14T17:55:58Z against /mnt/data/work/rumpun @ c973651: **6 PASS,
0 FAIL, 0 DRIFT, 47 SKIP**. Cross-checks with w2's independent pre-matrix
runs (table above): same six scripts, same verdicts. The 47 SKIPs are
archived module copies / fixture-bound suites / calibration + generator
scripts, each with the runner's reason in the matrix.

## REGRESSION fixes

None. The matrix proves zero REGRESSION verdicts against main @ c973651,
and w2's independent runs agree. No src/ patch was needed; the workspace
src/ directory is empty of patches. (Premise check: the season brief
expected merge-reconciliation drift; the empirical matrix found none.)

## DRIFT records

None with verdict DRIFT. Two accepted runner-side adaptations recorded by
w1 in the adapter table (script meaning unchanged, main unchanged):

- s18/w1-h6-loop.py hardcodes the repo src path by absolute path (accepted
  drift risk; verdict PASS, both-appends 0 of 20).
- s19/w1-repro-h2-h3.py expects src/ next to itself; the runner stages a
  copy with src/ symlinked to current repo src (verdict PASS).

## Verify before finishing (w2, 2026-09-15)

- ✅ Runner re-run against the patched tree (replica in scratch/repl:
  workspace tests copy + w1's real runner + main src copy): matrix emitted
  at the runner's default repo-root location, **6 PASS, 0 FAIL, 0 DRIFT,
  47 SKIP** — no REGRESSION verdicts remain (none were emitted to remove).
  Evidence: scratch/repl/replay-matrix.md (git line shows source c973651).
- ✅ Suite green with the pin included: **124 passed in 42.09s** (123
  historical + test_replay_matrix_has_no_regressions), exit 0. The pin ran
  w1's tools/replay_corpus.py end to end inside pytest (runner wall 9.6s).
  Evidence: scratch/repl/final-replica-suite.txt.
- ✅ ruff clean: workspace tests copy, line-length 100,
  --no-respect-gitignore (rimba/ rule), zero findings, on the exact
  shipped bytes.
- Deliverable mapping: REGRESSION fixes — none required, matrix-proven;
  DRIFT records — none with verdict DRIFT (two runner-side adaptations
  recorded above, main unchanged); regression pin — tests/test_rumpun.py
  append (workspace copy), proven on synthetic matrices (missing runner
  fails, REGRESSION row fails, PASS+SKIP passes) and green against the
  real runner.
- Merge note for the harness: the pin FAILS (never skips) when
  tools/replay_corpus.py is absent on main — merge w1's runner and this
  test file together.
