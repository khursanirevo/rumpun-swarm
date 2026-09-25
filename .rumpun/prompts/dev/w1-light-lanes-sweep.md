# s139 w1 — the light lanes re-run current

The steady-state mode's first live cycle: the guards already exist;
the lane runs them fresh and names any drift.

## Ground truth (measured 2026-09-21)
- the guards: tests/test_s136_full_guide_lint.py (the full guide),
  tests/test_s128_readme_verbs_lint.py (the readme table),
  tests/test_s136_route_probes.py (the serve table)
- the template: .rumpun/seasons/_steady-state.yaml (the s138 shape;
  the light lanes are its pipeline)
- fixture discipline: read-only pins; the one bounded route probe is
  the only network spend

## Task
1. Run the guards fresh (solo, current); re-probe one route bounded
   (glm-5.3, the s125/s132 precedent); confirm the serve table stands.
   Record the sweep in tests/test_s139_light_lanes_sweep.py (the
   sweep-record shape: the guards' versions, the probe result, the
   date; reads only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s139_light_lanes_sweep.py only. notes.md REQUIRED.
