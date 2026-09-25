# s137 w2 — the guide describes the steady-state mode

The campaign settled into a steady state: light lanes (lint, probe,
rehearse) keeping the machinery warm while the operator decides. The
guide's keep-going section should describe the mode.

## Ground truth (measured 2026-09-21)
- the section: docs/campaign-guide.md section 4 (keep going)
- the pattern: light lanes that keep the machinery warm without
  inventing work - the lint sweep, the route probes, the rehearsals -
  with the operator's decision gating anything heavier
- the guide's lint guard: tests/test_s121_campaign_guide.py and the
  s136 full-guide lint fail the suite when a command drifts
- fixture discipline: docs only; no src changes

## Task
1. Document the steady-state mode in section 4: what it is, the
   light-lane pattern, the operator's decision gate, and when to
   leave it (a fresh candidate class or the operator's word). The
   guide lint stays green. Pins: tests/test_s137_steady_state_doc.py
   (the section's commands lint, red-first if a command is added).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: docs/campaign-guide.md, tests/test_s137_steady_state_doc.py
  only. notes.md REQUIRED.
