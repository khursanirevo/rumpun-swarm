# s138 w2 — the steady-state season becomes a scaffold shape

The steady-state mode is documented in the guide; init does not emit
its season shape. First-class it.

## Ground truth (measured 2026-09-21)
- the scaffold: init emits s1.yaml, _template.yaml, and
  _competition.yaml (docs/campaign-guide.md's what-lands table; the
  s67 honest-placeholders design)
- the mode: docs/campaign-guide.md section 4 documents the steady
  state (the light lanes: the lint sweep, the route probes, the
  rehearsals; the operator's decision gate)
- the gate precedent: the emitted template lints clean by the
  honest-placeholders design; the wiped-fill copy refuses naming its
  errors (the positive control, the s127 shape)
- fixture discipline: init in tmp campaigns; the real campaign never
  written in tests

## Task
1. Land the template: init emits .rumpun/seasons/_steady-state.yaml
   (the light-lane shape: the lint sweep, the route probes, the
   rehearsal fields, the operator's decision gate in the band); the
   filled shape lints clean; the wiped-fill copy refuses naming its
   errors (the positive control). The guide's what-lands table names
   it. Pins red-first in tests/test_s138_steady_state_template.py
   (tmp campaigns).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/scaffold.py, docs/campaign-guide.md, tests/
  test_s138_steady_state_template.py only. notes.md REQUIRED.
