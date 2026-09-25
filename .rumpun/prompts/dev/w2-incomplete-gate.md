# s114 w2 — the harvest carries the incomplete mark

The gate marks a notes-less exit on the state snap and the results row;
the harvest record still reads clean. The record should say what the
gate saw.

## Ground truth (measured 2026-09-20)
- the mark: src/rumpun/engine.py _write_results writes the additive
  incomplete key into the results row (the s113 w2 row is the live
  exemplar: exit_code 0, incomplete "notes.md missing" - embed its
  shape, never copy .rumpun/runs/)
- the record builder: src/rumpun/harvest.py assembles the harvest
  record body; the close worker runs the verb (never call the harvest
  verb inside a fixture - it appends to the REAL ledger; hand-build the
  row and the record in tmp)
- the outcome rows: src/rumpun/runs/<sid>/verdicts.jsonl gains the
  season row at harvest; the body shape is pinned by earlier seasons

## Task
1. Land the gate: a harvest over a season whose results rows carry the
   incomplete key appends an incomplete line to the record body
   automatically (unit, the key's value); a clean season's record stays
   byte-identical in shape. Pins red-first in
   tests/test_s114_incomplete_gate.py (hand-built fixtures in tmp; the
   harvest VERB never runs against the real ledger in tests).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/harvest.py, tests/test_s114_incomplete_gate.py
  only. notes.md REQUIRED.
