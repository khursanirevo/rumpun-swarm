# s130 w1 — rehearse the honest exit before it is needed

The assessment module's verdict takes CONTINUE, PAUSE, EXHAUSTED; the
campaign has only ever sealed CONTINUE. The stop path should work the
day it is needed.

## Ground truth (measured 2026-09-20)
- the module: src/rumpun/audit.py usefulness_inputs and
  seal_usefulness_assessment (verdict CONTINUE, PAUSE, EXHAUSTED; the
  s118 adjusted-counts derivation rides the seal)
- the surfaces: the planner's drought hint (an EXHAUSTED newest seal is
  not "due" - exhausted campaigns are not asked to continue), the loop
- fixture discipline: tmp campaigns; akar.append_record for records;
  the real ledger never written in tests

## Task
1. Rehearse: an EXHAUSTED assessment seals through the module in a tmp
   campaign and reads back field-identical; the plan surface pinned for
   the exhausted state (the hint stays silent - the campaign is not
   asked to continue). Pins red-first in
   tests/test_s130_exhaustion_rehearsal.py.
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/audit.py or src/rumpun/evolve.py ONLY if a seam is
  needed, tests/test_s130_exhaustion_rehearsal.py. notes.md REQUIRED.
