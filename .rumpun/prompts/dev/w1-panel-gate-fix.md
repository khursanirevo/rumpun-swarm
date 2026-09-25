# s86 w1 — fix issue #13: the panel's suite gate reads the whole row

The gate refused three of five sweep requests because it reads one
cell of the ships row. The row is the surface.

## Ground truth (measured 2026-09-17)
- panel.py:144-147: the suite-claim scan takes the third cell of the
  ships row and searches only that cell for `suite N/N`
- the s80/s82 rows carry the claim in the verdict cell; the s81 row
  carries it nowhere (that row genuinely lacks one — its refusal is
  CORRECT and must stay)
- issues #11/#12 (route credits) are operator-side, not yours

## Task
1. Fix the scan: the suite-claim search spans the WHOLE ships row
   (all cells), so a claim in any cell satisfies the gate. The s81
   shape (no claim anywhere) still refuses, with the same message.
2. Verify against the real rows: `rumpun audit --panel s80 --dry-run`
   and `--panel s82 --dry-run` now pass the gate (route not called in
   dry-run); `--panel s81 --dry-run` still refuses with the named
   message.
3. Pins (tests/test_s86_w1_pins.py, _s86w1_ prefix, offline): the
   claim-in-any-cell acceptance (verdict cell, evidence cell, both),
   the nowhere refusal (the s81 shape), and the real s80/s81/s82 rows
   as fixtures.
4. notes.md REQUIRED: the diff, the three dry-run outputs.

## Bounds
- Edits: src/rumpun/panel.py, tests/. No route call. notes.md REQUIRED.
