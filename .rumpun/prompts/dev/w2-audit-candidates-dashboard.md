# s133 w2 — the dashboard carries the audit's candidates

The fronts card carries the decisions; the audit's current candidates
live in the ledger. One read should carry both.

## Ground truth (measured 2026-09-20)
- the surface: src/rumpun/report.py render_index (the fronts card, the
  lessons cell, the spend card are the precedents; the M1 contract)
- the candidates: the newest audit-* record's candidate lines
  (audit-48: three, all standing residuals; the detector names the
  repetition at plan time)
- the honest shape: present -> the card renders the candidates
  verbatim; absent -> byte-identical page
- fixture discipline: tmp campaigns; synthesize the audit record; no
  real writes

## Task
1. Land the candidates card: the report index renders the newest
   audit record's candidate lines when present; absent, byte-identical.
   Pins red-first in tests/test_s133_audit_candidates_dashboard.py
   (tmp fixtures).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/report.py, tests/test_s133_audit_candidates_dashboard.py
  only. notes.md REQUIRED.
