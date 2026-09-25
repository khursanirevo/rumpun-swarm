# s132 w1 — the campaign names its own candidate exhaustion

audit-48 named three candidates, every one a standing decade residual.
When the audits keep naming old residuals and nothing new, that is the
stopping rule firing - and the plan should say so for the operator.

## Ground truth (measured 2026-09-20)
- the hint pattern: src/rumpun/evolve.py (the s116 drought hint and the
  s122 date-window rule are the house style: plan-time, named, never
  blocking)
- the audit records: audit-* in .rumpun/ledger/ carry candidate lines;
  audit-48's three are all decade-1 residuals already standing
- the directive frame: the auto-continue runs until no more useful
  thing to do - the detector surfaces that moment, the operator decides
- fixture discipline: tmp campaigns with fixture audit records via
  akar.append_record; the real ledger never written in tests

## Task
1. Land the detector: when the most recent audit record's candidates
   all match candidates named in any earlier audit record (the
   repetition test), the plan output surfaces "the candidate pool is
   repeating: the operator decides" with the repeated count; fresh
   candidates stay silent. Pins red-first in
   tests/test_s132_exhaustion_detector.py (fixture records in tmp).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/evolve.py, tests/test_s132_exhaustion_detector.py
  only. notes.md REQUIRED.
