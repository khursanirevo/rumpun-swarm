# s43 w1 — reachable-artifact falsify + DRIFT mismatch arming (notes)

Date: 2026-09-15. All numbers below are measured in this session; raw output
sits in scratch/logs/ (baseline.log, patched.log, repro_falsify.log,
repro_drift.log, probe.log, lint.diff, audit.diff).

## Outcome

Both deliverables are implemented as patched copies under scratch/src,
repro'd, ruff-clean. The suite is green against them except one environment
pin that fails identically on the unpatched baseline.

- Deliverable 1: lint.py falsify gate demands a reachable artifact.
- Deliverable 2: audit.py DRIFT rows arm mismatch candidates.
- No s34 fixture needed adjusting: all five falsify pins pass unmodified.

## Changes

- scratch/src/rumpun/lint.py: the falsify_required gate now runs BEFORE the
  DAG check and demands a reachable reader: some phase whose reads name an
  artifact in the pipeline's writes set. A season whose readers all read
  artifacts nothing writes gets an error naming the season and the artifact,
  alongside the pre-existing DAG error. Zero-reader and campaign-scope
  behavior unchanged. Self-reads stay reachable (decision below).
- scratch/src/rumpun/audit.py: verdict-DRIFT matrix rows arm one
  "candidate: drift mismatch: <script> — assumptions moved (<note>)" per
  drifted script (first note wins, matrix order), right after the corpus
  regression candidate, before the cap. The regression candidate keeps its
  FIRST priority. The fresh-matrix finding drops the "all green" suffix when
  drifts armed. The module docstring lists the new trigger.
- Diffs vs repo src: scratch/logs/lint.diff, scratch/logs/audit.diff.

## Decision: self-reads stay reachable

- The brief's parenthetical "some other phase's writes names it" would reject
  a phase reading its own writes. I read the spec narrower: the repro targets
  "an artifact nothing writes", and a self-written artifact is written.
- Engine and benih fixtures (SEASON_S1, SEASON_DUAL) self-read and are
  linted in tests; rejecting self-reads would break fixtures the brief does
  not sanction touching, so the suite could not stay green.
- Reachability is membership in the pipeline's writes set (any phase). The
  DAG check still owns read/write shape.

## Evidence (all verified real this session)

- probe_path.py: both modules import from scratch/src (exit 0).
- repro_falsify.py (exit 0): foreign read errors naming s9 + phantom.jsonl
  ("falsify_required: season s9 has no reachable falsification input —
  'evaluate' reads 'phantom.jsonl': ..."); reachable reader: zero errors;
  self-read: zero errors; zero-reader s34 gate intact.
- repro_drift.py (exit 0): DRIFT-only matrix arms one candidate citing
  s10/drifted.py + its note; FAIL+DRIFT keeps regression first; all-green
  arms nothing; duplicate DRIFT rows dedupe (first note wins); fresh matrix
  arms and the finding line shows "2 PASS, 0 FAIL, 1 DRIFT, 0 SKIP" with no
  "all green" suffix.

- ruff: both patched files clean (line-length 100, --no-respect-gitignore).
- Suite, repo .venv pytest 9.1.1, PYTHONPATH=scratch/src:
  baseline (repo src): 187 passed, 1 failed in 68s.
  patched (scratch src): 187 passed, 1 failed in 219s.
  The 1 is test_s38_coldstart_checker_leaves_repo_rumpun_untouched: its
  sha256 snapshot over the repo .rumpun tree caught the sibling worker's
  live .rumpun/rimba/s43/w2/{agent.log,state.json} changing mid-run. The
  same pin fails on the unpatched baseline. Not a code regression; rerun
  when the season is idle.

## Incidents

- Three corrupted writes while drafting the repro scripts (leaked drafting
  tokens, truncation, and one Write to a wrong path outside the workspace,
  since removed). Rebuilt in chunks of at most 15 lines with py_compile and
  run gates after every step. The six src Edits applied cleanly and are
  diff-gated (scratch/logs/*.diff).

## Left for w2 / the harness

- w2 owns the pins: foreign-read error naming season + artifact, reachable
  reader passes, DRIFT arming, regression priority, dedupe, green-suffix.
- Merge applies the two diffs to src/rumpun/{lint,audit}.py.
