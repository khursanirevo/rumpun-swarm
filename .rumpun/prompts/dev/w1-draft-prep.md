# s120 w1 — the loop hands the draft to the worker

The close-prep record reserves the close; the next yaml still gets
drafted by hand each time. The loop can draft it - never launch,
harvest, or commit it.

## Ground truth (measured 2026-09-20)
- the close-prep: src/rumpun/loop.py (the s119 record: season id,
  completed-at, the worker's duty reserved)
- the planner: src/rumpun/evolve.py draft drafts the next season yaml
  from the parent (the same output the close chain fills)
- the hard rule: the loop NEVER harvests, seeds, launches, or commits;
  the draft lands in the season's run dir (gitignored live state),
  and the worker moves and fills it under .rumpun/seasons/
- fixture discipline: tmp campaigns; the harvest verb never runs in a
  test; no real ledger writes

## Task
1. Extend the prep: the close-prep record gains the drafted yaml (the
   planner's own draft function, written into the run dir), the path
   named in the record. Idempotent: one record and one draft per
   season. The worker's fill-and-launch duty stays named. Pins
   red-first in tests/test_s120_draft_prep.py (fixture campaigns in
   tmp; no real ledger writes).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/loop.py, tests/test_s120_draft_prep.py only.
  notes.md REQUIRED.
