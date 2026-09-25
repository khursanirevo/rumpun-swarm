# s127 w2 — the report renders the attested commit

The results rows carry each lane's commit since s123; the report page
does not show it. The operator reads the report; the attestation
should render there.

## Ground truth (measured 2026-09-20)
- the row truth: src/rumpun/engine.py _write_results writes the
  additive commit key when HEAD moved past the season's start HEAD
  (the s123 machinery, attested in production at s124 and s125)
- the report: src/rumpun/report.py renders from persisted files alone
  (the M1 determinism contract; the s113 marks and the s124 stall
  marks are the precedents)
- fixture discipline: synthesize results rows in tmp; never copy
  .rumpun/runs/ (the check-s110 class)

## Task
1. Extend the report: an agent row whose results entry carries the
   commit key renders the sha; rows without stay byte-identical (the
   M1 contract holds). Pins red-first in
   tests/test_s127_report_commit_mark.py (synthesized rows in tmp).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/report.py, tests/test_s127_report_commit_mark.py
  only. notes.md REQUIRED.
