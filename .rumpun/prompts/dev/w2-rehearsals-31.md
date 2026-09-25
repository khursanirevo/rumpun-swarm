# s176 w2 — the rehearsals re-run fresh

The steady-state cycle repeating: the rehearsal guards run fresh,
any drift names itself, the reconfirmation record lands.

## Ground truth (measured 2026-09-21)
- the guards: tests/test_s130_exhaustion_rehearsal.py and
  tests/test_s130_guide_walkthrough.py
- the precedent: the s139/s144/s148/s149/s150/s152/s153/s154/s155/
  s156/s157/s158/s159/s160/s161/s162/s163/s164/s165/s166/s167/s168/
  s169/s170/s171/s172/s173/s174/s175 reconfirmation records (s151's
  read-only carry-forward sits between them); notes.md REQUIRED
  (s175's both-lane gap is the caution)
- fixture discipline: the guards are tmp-campaign tests; running them
  writes nothing real

## Task
1. Run both rehearsal guards fresh; confirm green; name any drift.
   Record the reconfirmation in tests/test_s176_rehearsals_31.py (the
   record shape: the date, the outcome, one pinned sha256 per guard;
   reads only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now;
  s175's gap is the caution). Never wait on a background job at turn
  end.

## Bounds
- Edits: tests/test_s176_rehearsals_31.py only. notes.md REQUIRED.
