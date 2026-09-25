# s100 w1 — the ships-row surface gate: the 8-fire class closes structurally

Eight fires s63-s95: ships rows kept naming surfaces wrong (short
paths, bare basenames, unnamed tokens) and the checker kept catching
them one rename at a time. The structural repair: stop trusting the
row's naming — derive what you can from the committed tree itself.

## Ground truth (measured 2026-09-18)
- the 8-fire record: RESUME's corrections line (check-s67 through
  check-s94); w2's s99 front table names the class
- the checker: tools/artifact_check.py — the ships-row diff parses
  the row's tokens for surface names (the token classes: short
  relatives, bare basenames, unnamed nouns)
- the s83 precedent: the seal-time-lint moved a check from convention
  to gate — the same structural move, different surface

## Task
1. Design the structural repair per the code's shape: the options —
   (a) the ships-row TEMPLATE gains the surface columns (the writer
   fills structured fields, not prose), or (b) the checker derives
   candidate surfaces from the committed tree (files changed in the
   close commit are the candidate set; the row's prose must reference
   them, not invent names), or (c) both. Choose per the code's
   reality; the contract: a row naming a surface that does not exist
   in the tree is caught AT DESIGN-WRITING TIME (a lint pass on the
   DESIGN entry), not at check time — the shift left is the repair.
2. Land it: the DESIGN-entry lint (or the template columns) with
   pins (tests/test_s100_w1_pins.py, _s100w1_ prefix, offline): a row
   naming a nonexistent surface fails the lint with the token named;
   a row naming real surfaces passes.
3. Verify: the s79-s95-era bad rows (the corrections line's shapes)
   fail the new lint; the good rows (the reworded ones) pass.
4. notes.md REQUIRED: the design, the pin list, the bad-row
   verifications.

## Bounds
- Edits: src/rumpun/ (the lint home), DESIGN.md (only if the lint
  flags the CURRENT rows — fix those rows to real surfaces), tests/.
  notes.md REQUIRED.
