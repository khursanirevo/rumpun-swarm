# s122 w1 — the drought counts every usefulness convention (issue #38)

Two usefulness conventions exist and the drought rule sees one. The
decade reviews seal usefulness-decade-<N> records; the cadence walk
counts only usefulness-s<N>. A decade seal does not stop the walk.

## Ground truth (measured 2026-09-20)
- the rule: src/rumpun/evolve.py _ASSESSMENT_CADENCE_CLOSES (6),
  _USEFULNESS_SEAL_RE (the usefulness-s<N> shape), _assessment_due
  (the parent-chain walk; the cycle guard)
- the two series in .rumpun/ledger/: usefulness-s87, -s97, -s98, -s99,
  -s101, -s104, -s107, -s114, -s121 (assessments) and
  usefulness-decade-1 through -6 (decade reviews) - both are standing
  usefulness judgments
- the filing: issue #38 on the live board, filed after the s114 seal
- fixture discipline: tmp campaigns; records via akar.append_record;
  the real ledger never written in tests

## Task
1. Reconcile: pick the honest semantics (a decade review IS a
   usefulness seal for cadence purposes, or the rule counts both
   series and names which stopped the walk), implement, and pin the
   boundary red-first - a decade seal inside the window silences the
   hint; the announcement names which record stopped the drought.
   Pins in tests/test_s122_drought_reconcile.py.
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/evolve.py, tests/test_s122_drought_reconcile.py
  only. notes.md REQUIRED.
