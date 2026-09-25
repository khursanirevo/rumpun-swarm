# s140 w2 — the steady-state cycle's second iteration

The first cycle proved the mode; the second proves it repeats. Run
the light lanes and the rehearsals fresh, name any drift.

## Ground truth (measured 2026-09-21)
- the guards: tests/test_s136_full_guide_lint.py,
  tests/test_s128_readme_verbs_lint.py,
  tests/test_s136_route_probes.py,
  tests/test_s139_light_lanes_sweep.py,
  tests/test_s139_rehearsals_reconfirm.py,
  tests/test_s130_exhaustion_rehearsal.py,
  tests/test_s130_guide_walkthrough.py
- the first cycle: s139's records (the sweep and the reconfirmation)
  are the comparison point
- fixture discipline: read-only; the one bounded route probe is the
  only network spend

## Task
1. Run the light-lane guards and the rehearsal guards fresh; re-probe
   one route bounded; name any drift. Record the second iteration in
   tests/test_s140_steady_sweep_2.py (the record shape: the guards'
   versions, the probe result, the date; reads only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s140_steady_sweep_2.py only. notes.md REQUIRED.
