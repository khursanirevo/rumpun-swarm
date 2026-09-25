# s137 w1 — the index shows what is running right now

The report index shows completed history; a running season is
invisible on it. The operator's glance should answer "what is
running".

## Ground truth (measured 2026-09-21)
- the surface: src/rumpun/report.py render_index (the fronts, lessons,
  spend, candidates cards are the precedents)
- the M1 contract: render from persisted files alone - the state.json
  status field and started_at are persisted, so the card names the
  running season and its started_at, never the live elapsed
- the honest shape: a running season -> the card names it; none ->
  byte-identical page
- fixture discipline: tmp campaigns; synthesize the state files; no
  real writes

## Task
1. Land the card: the report index renders a running-season cell
   (season id, started_at) when a persisted state reads running;
   absent, byte-identical page. Pins red-first in
   tests/test_s137_running_card.py (tmp fixtures).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/report.py, tests/test_s137_running_card.py only.
  notes.md REQUIRED.
