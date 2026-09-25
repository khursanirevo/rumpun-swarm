# s26 w2 — spec-first pins for the matrix-ingesting audit

Scope: 5 added pins in workspace `tests/test_rumpun.py` (additions-only vs
the repo file; no existing test modified). Baseline commit 03cae74 (s25 win
lands corpus gate; s26 seeded). w1 owns src/rumpun/audit.py; these pins
spec the ingestion contract w1 implements. The pins are red against
pre-s26 code by design; the harness merges.

## Measured red set (vs pre-s26 audit.py @ 03cae74)

| pin | red reason (measured, scratch/full-pin-run.txt) |
|---|---|
| test_audit_ingests_newest_evidence_matrix | 0 corpus candidates; run_audit never reads any matrix |
| test_audit_corpus_candidate_first_under_cap | no corpus candidate; priority is phase->route->calibration; calibration present among candidates |
| test_audit_all_green_matrix_is_finding_never_candidate | no corpus finding exists in output |
| test_audit_malformed_matrix_rows_skipped_with_one_debug_each | 0 candidates, 0 DEBUG records (no ingestion at all) |
| test_audit_without_matrix_byte_identical_to_pre_s26 | GREEN by construction — see A/B below |

Raw: `scratch/red-set.txt` (4 failed, 125 deselected, 0.22s);
`scratch/full-pin-run.txt` (124 passed, 5 failed, 32.24s).

## Baseline and existing-suite regression

- Baseline at repo location, pre-work: `python -m pytest tests/ -q` ->
  **124 passed** in 44.02s, exit 0. Evidence: scratch/baseline-suite.txt.
- Workspace copy run: 124 passed, 5 failed. The 5: my 4 intended-red pins
  + `test_replay_matrix_has_no_regressions` (s25 pin). That pin is
  location-bound: it derives the repo root from `parents[1]` of the test
  file, so from the w2 workspace it finds no tools/replay_corpus.py.
  Green at repo location (baseline-suite.txt). Merging my additions into
  the repo tests file restores it. Additions-only held.
- typo note: pin name is test_replay_matrix_has_no_regressions (notes line above has a typo).

## A/B golden (backward-compat pin)

- GOLDEN_PRE_S26_BODY: 10 exact body lines of the audit-1 record over the
  _audit_base fixture, captured from pre-s26 code via physical script
  scratch/capture_golden.py -> scratch/golden.json. Not hand-transcribed;
  the pin comparing against the literal is green, which proves the
  transcription byte-exact.
- The pin also requires: evidence dirs present but no replay-matrix.md ->
  same body; no "corpus" substring anywhere; record header (date line)
  excluded from comparison (body = record lines[4:-1]).
- Expected post-merge: stays green. Red post-merge = w1's patch changed
  no-matrix behavior; that is a w1 defect, not a pin bug.

## Contract decisions w1 must match (merge reconciliation points)

- Discovery: newest replay-matrix.md across akar/evidence/<dir>/
  replay-matrix.md. Newest must be numeric-aware: the s9/s10 fixture goes
  red under a lexicographic sort; mtime agrees with numeric in the pin.
  If w1 lands a canonical path outside evidence/ instead, pin 1 needs
  reconciliation (my spec: "under akar evidence").
- Arming: any FAIL row (note naming REGRESSION or not) arms exactly one
  corpus candidate per arming row. Candidate: starts "candidate:",
  contains "corpus regression" + script + first failing line. A literal
  REGRESSION verdict token arms the same. Multi-FAIL-row count is
  unpinned (one vs per-row arming is w1's call).
- Priority + cap: corpus candidate is candidates[0] ahead of phase/route/
  calibration; with 4 triggers -> 3 candidates (MAX_CANDIDATES) and the
  "unproposed here" line naming LOSS band calibration.
- All-green: one finding line, contains "corpus:" and "N repro scripts
  green" with N = PASS-row count (pinned at N=2); no candidates;
  "candidates: none" line stays.
- Malformed: non-structural rows (<4 cells, empty script, non-verdict
  second cell) -> exactly one DEBUG each from logger "rumpun.audit";
  header and separator rows are structure, not malformed. A valid FAIL row
  in the same matrix still arms. If w1's parser also DEBUG-logs the
  header/separator, the ==3 count needs merge reconciliation.
- DRIFT rows: unpinned — neither candidate-arming nor all-green-blocking
  is asserted; w1's implementation decides.
- A/B golden covers the _audit_base fixture only; richer fixtures are not
  byte-frozen.

## Verification artifacts (scratch/)

- baseline-suite.txt — 124 passed pre-work (repo location, 44.02s)
- capture_golden.py + golden.json — golden capture, executable evidence
- red-set.txt — the 4 measured red pins vs pre-s26 code
- full-pin-run.txt — full workspace file: 124 passed / 5 failed, reasons inline
- ruff check --no-respect-gitignore on the workspace file: All checks passed
