# s149 w1 — the light lanes re-run current

The steady-state cycle continuing: the guards run fresh, one bounded
probe re-confirms, the sweep record lands.

## Ground truth (measured 2026-09-21)
- the guards: tests/test_s136_full_guide_lint.py,
  tests/test_s128_readme_verbs_lint.py,
  tests/test_s136_route_probes.py,
  tests/test_s139_light_lanes_sweep.py,
  tests/test_s140_steady_sweep_2.py,
  tests/test_s147_light_lanes_3.py,
  tests/test_s148_light_lanes_4.py (the fourth-iteration record is the
  shape precedent)
- the probe precedent: one bounded glm-5.3 call (the s125/s132/s139
  trail; the catalog warning is CLI-side text)
- fixture discipline: read-only; the probe is the only network spend

## Task
1. Run the guards fresh; re-probe one route bounded; name any drift.
   Land the sweep record in tests/test_s149_light_lanes_5.py (the
   record shape: the guards' sha256 versions, the probe result, the
   date; reads only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s149_light_lanes_5.py only. notes.md REQUIRED.
