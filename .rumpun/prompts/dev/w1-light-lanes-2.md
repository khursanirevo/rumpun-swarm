# s144 w1 — the light lanes re-run current

The steady-state cycle's next iteration: the guards run fresh, one
bounded route probe re-confirms, any drift names itself.

## Ground truth (measured 2026-09-21)
- the guards: tests/test_s136_full_guide_lint.py,
  tests/test_s128_readme_verbs_lint.py,
  tests/test_s136_route_probes.py,
  tests/test_s139_light_lanes_sweep.py
- the probe precedent: one bounded glm-5.3 call (the s125/s132/s139
  trail; the catalog warning is CLI-side text)
- fixture discipline: read-only; the probe is the only network spend

## Task
1. Run the guards fresh; re-probe one route bounded; name any drift.
   Record the sweep in tests/test_s144_light_lanes_2.py (the record
   shape: the guards' sha256 versions, the probe result, the date;
   reads only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s144_light_lanes_2.py only. notes.md REQUIRED.
