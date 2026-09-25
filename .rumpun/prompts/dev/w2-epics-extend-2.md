# s97 w2 — the board arc extends; the assessment composition pinned

Maintenance with the arithmetic pinned: the board arc gains s96, and
the s88 assessment module's composition gets its first contract pins
(the module has pins for the vocabulary but none for the composition
shape w1's seal exercises).

## Ground truth (measured 2026-09-18)
- .rumpun/epics.yaml: board-arc carries s69-s95; s96 sits in the
  campaign epic (it closed after the s95 extension)
- audit.py: seal_usefulness_assessment composes the s87 shape
  (verdict, basis, fronts with owners, the satisfied header) and
  refuses bad shapes (AuditError); w1 seals the s97 assessment
  through it this season
- the pinned arithmetic: the two epic views sum to the whole ledger

## Task
1. Extend the board-arc epic: epics.yaml gains s96. Preserve every
   verdict (the pinned arithmetic).
2. Verify the epic view: the two views sum to the whole ledger; lint
   passes.
3. Pins (tests/test_s97_w2_pins.py, _s97w2_ prefix, offline): the
   assessment composition's shape — a fixture front set composes to
   the s87 byte-shape (verdict line, basis line, the front lines'
   owner/next fields, the satisfied header); the AuditError refusals
   (empty name, the ` - owner: ` collision, the `. ` in the owner)
   refuse with the named messages.
4. notes.md REQUIRED: the epic view output, the pin map.

## Bounds
- Edits: .rumpun/epics.yaml, tests/. No route call. notes.md
  REQUIRED.
