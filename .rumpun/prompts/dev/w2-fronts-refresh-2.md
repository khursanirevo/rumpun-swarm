# s145 w2 — the fronts file refreshed current

The fronts file drifts as closes land; the refresh is the recurring
maintenance lane. Refresh to the RESUME open items verbatim.

## Ground truth (measured 2026-09-21)
- the file: .rumpun/operator-fronts.yaml (the s138 refresh; the s131
  render pins standing)
- the truth: .rumpun/RESUME.md's open items (the standing decisions'
  source)
- the format pins: tests/test_s138_fronts_refresh.py (the file parses
  as a list of non-empty strings, every entry names its owner)

## Task
1. Refresh the fronts file to the RESUME open items verbatim (the
   standing decisions, current as of this close). Re-run the s138
   format pins green. Land the refresh record in
   tests/test_s145_fronts_refresh_2.py (the record shape: the date,
   the entries, reads only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: .rumpun/operator-fronts.yaml,
  tests/test_s145_fronts_refresh_2.py only. notes.md REQUIRED.
