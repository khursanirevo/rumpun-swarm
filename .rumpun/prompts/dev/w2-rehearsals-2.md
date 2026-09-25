# s144 w2 — the rehearsals re-run fresh

The steady-state cycle's next iteration: the rehearsal guards run
fresh, any drift names itself.

## Ground truth (measured 2026-09-21)
- the guards: tests/test_s130_exhaustion_rehearsal.py and
  tests/test_s130_guide_walkthrough.py
- the precedent: the s139/s140 reconfirmation records
- fixture discipline: the guards are tmp-campaign tests; running them
  writes nothing real

## Task
1. Run both rehearsal guards fresh; confirm green; name any drift.
   Record the reconfirmation in tests/test_s144_rehearsals_2.py (the
   record shape: the guards' versions, the date, the outcome; reads
   only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s144_rehearsals_2.py only. notes.md REQUIRED.
