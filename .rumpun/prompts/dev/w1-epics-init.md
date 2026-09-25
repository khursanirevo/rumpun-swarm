# s85 w1 — epics --init: the board arc becomes the first epic

The decision deferred twice lands now: `rumpun epics --init` scaffolds
the epic rollup over the season history that already exists.

## Ground truth (measured 2026-09-17)
- epics.py (s58): the epic rollup VIEWS over ledger records; the verb
  family exists (rumpun epics); --init has never run on this campaign
- the natural first epic: the board arc (s69-s84 — the GitHub home,
  the board, the lifecycle, the map, the pulled seasons, the residuals)
- the board map works: board --map s85 <issue url> at close

## Task
1. Run `rumpun epics --init` on the campaign (per epics.py's contract;
   read the module first). Record what it creates.
2. Verify the rollup: the board arc seasons (s69-s84) roll into one
   epic view with their verdicts; the view reads the ledger only
   (no new state).
3. If --init needs arguments the module does not self-describe, adapt
   minimally and record the interface gap in notes.md (an issue draft
   if it is a real defect).
4. notes.md REQUIRED: what --init created, the epic view output, any
   gap found.

## Bounds
- Edits: src/rumpun/epics.py only if --init is missing or broken
  (minimal; pins in tests/test_s85_w1_pins.py, _s85w1_ prefix).
- notes.md REQUIRED. No .rumpun state edits beyond what the verb
  itself creates.
