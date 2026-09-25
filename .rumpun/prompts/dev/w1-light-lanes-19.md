# s163 w1 — the light lanes re-run current

The steady-state cycle repeating: the guards run fresh, one bounded
probe re-confirms, the sweep record lands.

## Ground truth (measured 2026-09-21)
- the guards: tests/test_s136_full_guide_lint.py,
  tests/test_s128_readme_verbs_lint.py,
  tests/test_s136_route_probes.py,
  tests/test_s139_light_lanes_sweep.py,
  tests/test_s140_steady_sweep_2.py,
  tests/test_s147_light_lanes_3.py,
  tests/test_s148_light_lanes_4.py,
  tests/test_s149_light_lanes_5.py,
  tests/test_s150_light_lanes_6.py,
  tests/test_s152_light_lanes_8.py,
  tests/test_s153_light_lanes_9.py,
  tests/test_s154_light_lanes_10.py,
  tests/test_s155_light_lanes_11.py,
  tests/test_s156_light_lanes_12.py,
  tests/test_s157_light_lanes_13.py,
  tests/test_s158_light_lanes_14.py,
  tests/test_s159_light_lanes_15.py,
  tests/test_s160_light_lanes_16.py,
  tests/test_s161_light_lanes_17.py,
  tests/test_s162_light_lanes_18.py (the last landed record)
- the probe precedent: one bounded glm-5.3 call (the s125/s132/s139
  trail; the catalog warning is CLI-side text; the `models --probe`
  verb stays broken — use the direct pinned call)
- fixture discipline: read-only; the probe is the only network spend

## Task
1. Run the guards fresh; re-probe one route bounded; name any drift.
   Land the sweep record in tests/test_s163_light_lanes_19.py (the
   record shape: the guards' sha256 versions, the probe result, the
   date; reads only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now;
  s162's w1 gap is the caution). Never wait on a background job at
  turn end.

## Bounds
- Edits: tests/test_s163_light_lanes_19.py only. notes.md REQUIRED.
