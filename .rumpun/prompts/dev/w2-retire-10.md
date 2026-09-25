# s86 w2 — retire issue #10 on the landed evidence + pin the gate's contract

Issue #10 (distill skips the content lint) was fixed in s83 — the
draft carries its files through the seal-time lint and the parent-
escape detector joined it. The issue was never closed on that
evidence. Your lane: retire it properly, then pin the gate contract
w1 fixes from the other side.

## Ground truth (measured 2026-09-17)
- s83 landed: every file under a draft passes the seal-time lint at
  its last seal; the parent-escape detector joined (PARENT_ESCAPE_RE);
  the pre-fix silent destruction recorded as red evidence
- issue #10 OPEN on the board; w1 fixes the panel gate (issue #13)
  this season
- the retirement pattern: the s79-style comment carries the sealed
  evidence, then the close

## Task
1. Retire #10: comment it with the s83 evidence (the carry-forward
   fix, the parent-escape detector, the red-before/green-after pins)
   citing the sealed s83-harvest record, then close it.
2. Pins (tests/test_s86_w2_pins.py, _s86w2_ prefix, offline): the
   panel gate's row-wide contract from the other side — adversarial
   shapes (claim in every cell, in no cell, split across cells),
   asserting w1's landed scan accepts or refuses each per the
   contract, never silent.
3. notes.md REQUIRED: the retirement evidence, the pin map.

## Bounds
- Edits: tests/ only (w1 owns panel.py). No live route call. notes.md
  REQUIRED.
