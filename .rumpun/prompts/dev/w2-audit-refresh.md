# s141 w2 — the audit refresh feeds the detector

The detector reads the newest audit record's candidates; a fresh audit
either repeats them or names a fresh class. Refresh and read.

## Ground truth (measured 2026-09-21)
- the verb: rumpun audit --last 5 (appends one candidates record per
  run; audit-48's three candidates are all standing decade residuals)
- the detector: src/rumpun/evolve.py _candidate_exhaustion (the
  repetition test the s132 lane landed)
- the honest record: the comparison names the repetition or the fresh
  class - both are the truth the detector needs
- fixture discipline: reads only; the audit verb itself writes the
  record (its designed behavior); no other writes

## Task
1. Run audit --last 5 fresh; read the newest audit record's
   candidates; compare to audit-48's (the repetition or the fresh
   class named). Record the comparison in
   tests/test_s141_audit_refresh.py (the record shape: the newest
   audit id, the candidates, the repetition verdict; reads only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s141_audit_refresh.py only. notes.md REQUIRED.
