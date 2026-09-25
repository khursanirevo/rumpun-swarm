# s138 w1 — the fronts file reflects the standing truth

The operator dashboard reads .rumpun/operator-fronts.yaml; the file
was seeded at s131 and drifts from the RESUME open items as closes
land. The lane refreshes it and pins the format.

## Ground truth (measured 2026-09-21)
- the file: .rumpun/operator-fronts.yaml (the s131 seed: the forge
  table, issue #18, the external workload, the kancil upgrade)
- the truth: .rumpun/RESUME.md's open items (the standing decisions'
  source) and the strict-xfail kancil alarm
- the render: src/rumpun/report.py render_index reads the file (the
  s131 pins cover the render); the file's format is the pin's subject
- fixture discipline: the pins read the real file read-only and
  synthesize fixtures for the malformed shapes

## Task
1. Refresh the fronts file to match the RESUME open items verbatim
   (the four standing decisions, current as of this close). Land the
   format pin: the file parses as a list of non-empty strings, and
   every entry names its owner. Pins in
   tests/test_s138_fronts_refresh.py (the malformed shapes red).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: .rumpun/operator-fronts.yaml, tests/test_s138_fronts_refresh.py
  only. notes.md REQUIRED.
