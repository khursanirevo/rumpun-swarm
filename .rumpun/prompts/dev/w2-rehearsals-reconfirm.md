# s139 w2 — the rehearsals re-run current

The steady-state mode's second light lane: the exhaustion rehearsal
and the guide walkthrough already exist as guards; the lane runs them
fresh and names any drift.

## Ground truth (measured 2026-09-21)
- the guards: tests/test_s130_exhaustion_rehearsal.py (the exhausted
  verdict round-trip) and tests/test_s130_guide_walkthrough.py (the
  guide's happy path end to end)
- the template: .rumpun/seasons/_steady-state.yaml (the rehearsals are
  its third light lane)
- fixture discipline: the guards are tmp-campaign tests; running them
  writes nothing real

## Task
1. Run both rehearsal guards fresh; confirm green; name any drift.
   Record the reconfirmation in tests/test_s139_rehearsals_reconfirm.py
   (the record shape: the guards' versions, the date, the outcome;
   reads only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s139_rehearsals_reconfirm.py only. notes.md
  REQUIRED.
