# s118 w1 — the assessment reads the adjusted truth

The s117 rollup renders the adjusted view; the assessment inputs still
read raw counts. The next seal should judge on adjusted truth.

## Ground truth (measured 2026-09-20)
- the seam: src/rumpun/audit.py usefulness_inputs and
  seal_usefulness_assessment (the s88 w2 lane; the s114 citation gate
  re-reads cited bodies fresh)
- the adjusted truth: src/rumpun/epics.py ADJUSTING_DISSENTS and the
  s117 adjusted counting (a WIN member whose dissent is INCONCLUSIVE
  or NEUTRAL adjusts; raw counts stay verbatim)
- the review's residual, verbatim: "usefulness-s114 preserves WIN
  totals despite s79's NEUTRAL and s83's INCONCLUSIVE second opinions"
- fixture discipline: tmp campaigns; akar.append_record for records;
  never write the real ledger in tests

## Task
1. Extend the assessment inputs: the inputs carry each epic's adjusted
   counts beside the raw ones (raw verbatim, adjusted named); the next
   seal's record body shows both. Nothing rewritten. Pins red-first in
   tests/test_s118_assessment_adjusted.py.
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/audit.py, tests/test_s118_assessment_adjusted.py
  only. notes.md REQUIRED.
