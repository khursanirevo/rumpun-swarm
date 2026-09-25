# s141 w1 — the steady-state cycle's third iteration

The mode proved it repeats at the second iteration; the third proves
the cadence holds. Run the light lanes and the rehearsals fresh.

## Ground truth (measured 2026-09-21)
- the guards: tests/test_s136_full_guide_lint.py,
  tests/test_s128_readme_verbs_lint.py,
  tests/test_s136_route_probes.py,
  tests/test_s139_light_lanes_sweep.py,
  tests/test_s139_rehearsals_reconfirm.py,
  tests/test_s140_steady_sweep_2.py,
  tests/test_s130_exhaustion_rehearsal.py,
  tests/test_s130_guide_walkthrough.py
- the second iteration: s140 w2's record is the comparison point
- fixture discipline: read-only; the one bounded route probe is the
  only network spend

## Task
1. Run the light-lane guards and the rehearsal guards fresh; re-probe
   one route bounded; name any drift. Record the third iteration in
   tests/test_s141_third_iteration.py (the record shape: the guards'
   versions, the probe result, the date; reads only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s141_third_iteration.py only. notes.md REQUIRED.
