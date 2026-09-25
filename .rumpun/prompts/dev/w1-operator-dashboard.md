# s131 w1 — the standing decisions surface where the operator reads

The operator-gated items live in RESUME open items and the ledger;
the operator reads the report. The index should carry the standing
decisions.

## Ground truth (measured 2026-09-20)
- the surface: src/rumpun/report.py render_index (the s129 lessons
  precedent: present -> a cell, absent -> byte-identical silence; the
  M1 contract)
- the truth: .rumpun/operator-fronts.yaml (a small campaign file the
  operator or the close worker maintains: one entry per standing
  decision - the forge table, issue #18, the kancil upgrade, the
  external workload)
- the honest shape: the file present -> the index renders one cell
  per entry; absent or empty -> byte-identical page
- fixture discipline: tmp campaigns; synthesize the fronts file; no
  real writes

## Task
1. Land the dashboard: the report index renders the fronts file's
   entries (one cell per entry, verbatim text); absent or empty ->
   byte-identical page. Pins red-first in
   tests/test_s131_operator_dashboard.py (tmp fixtures).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/report.py, .rumpun/operator-fronts.yaml,
  tests/test_s131_operator_dashboard.py only. notes.md REQUIRED.
