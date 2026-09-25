# s198 w1 — the light lanes re-run current

The steady-state cycle repeating: the guards run fresh, one bounded
probe re-confirms, the sweep record lands.

## Ground truth (measured 2026-09-22)
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
  tests/test_s162_light_lanes_18.py,
  tests/test_s163_light_lanes_19.py,
  tests/test_s164_light_lanes_20.py,
  tests/test_s165_light_lanes_21.py,
  tests/test_s166_light_lanes_22.py,
  tests/test_s167_light_lanes_23.py,
  tests/test_s168_light_lanes_24.py,
  tests/test_s169_light_lanes_25.py,
  tests/test_s170_light_lanes_26.py,
  tests/test_s171_light_lanes_27.py,
  tests/test_s172_light_lanes_28.py,
  tests/test_s173_light_lanes_29.py,
  tests/test_s174_light_lanes_30.py,
  tests/test_s175_light_lanes_31.py,
  tests/test_s176_light_lanes_32.py,
  tests/test_s177_light_lanes_33.py,
  tests/test_s178_light_lanes_34.py,
  tests/test_s179_light_lanes_35.py,
  tests/test_s180_light_lanes_36.py,
  tests/test_s181_light_lanes_37.py,
  tests/test_s182_light_lanes_38.py,
  tests/test_s183_light_lanes_39.py,
  tests/test_s184_light_lanes_40.py,
  tests/test_s185_light_lanes_41.py,
  tests/test_s186_light_lanes_42.py,
  tests/test_s187_light_lanes_43.py,
  tests/test_s188_light_lanes_44.py,
  tests/test_s189_light_lanes_45.py,
  tests/test_s190_light_lanes_46.py,
  tests/test_s191_light_lanes_47.py,
  tests/test_s192_light_lanes_48.py,
  tests/test_s193_light_lanes_49.py,
  tests/test_s194_light_lanes_50.py,
  tests/test_s195_light_lanes_51.py,
  tests/test_s196_light_lanes_52.py,
  tests/test_s197_light_lanes_53.py (the last landed record)
- the probe precedent: one bounded glm-5.3 call (the s125/s132/s139
  trail; the catalog warning is CLI-side text; the `models --probe`
  verb stays broken — use the direct pinned call)
- fixture discipline: read-only; the probe is the only network spend

## Task
1. Run the guards fresh; re-probe one route bounded; name any drift.
   Land the sweep record in tests/test_s198_light_lanes_54.py (the
   record shape: the guards' sha256 versions, the probe result, the
   date; reads only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now;
  both lanes shipped at s197 - keep it met). Never wait on a
  background job at turn end.

## Bounds
- Edits: tests/test_s198_light_lanes_54.py only. notes.md REQUIRED.
