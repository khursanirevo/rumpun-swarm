# s132 w2 — the dashboard carries the spend

Issue #18's measurable half: the campaign knows its writer-seconds and
never totals them. The operator dashboard should carry the sum.

## Ground truth (measured 2026-09-20)
- the surface: src/rumpun/report.py render_index (the s131 fronts card
  and the s129 lessons cell are the precedents; the M1 contract)
- the committed truth: the DESIGN.md season entries carry each
  season's writer-seconds in the harvest text ("both fable writers
  exited 0 at N s"); the gitignored results rows are not a committed
  source, so the sum parses DESIGN (the check-s83 lesson: counts come
  from committed sources)
- the honest scope: this is the measurable half of issue #18 - billing
  and operator-time stay the operator's
- fixture discipline: tmp campaigns; synthesize the DESIGN text; no
  real writes

## Task
1. Land the aggregation: the report index renders a spend cell (the
   total writer-seconds parsed from the committed season record);
   absent data -> byte-identical page. Pins red-first in
   tests/test_s132_spend_aggregation.py (tmp fixtures).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/report.py, tests/test_s132_spend_aggregation.py
  only. notes.md REQUIRED.
