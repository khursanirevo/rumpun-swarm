# s91 w2 — the repro-backed closure, applied to the campaign's own defect

Issue #17 is the first campaign defect with a live repro. Your slice:
the pin stabilizes red-before/green-after — the s80 standard eating
its own cooking — and the closure contract gets its teeth.

## Ground truth (measured 2026-09-17)
- issue #17 (OPEN): the h6-loop repro, 1/20 barrier races
- the repro-backed-closure contract (s80, in the kancil-base pack):
  a defect-resolving season closes only against the issue's own repro
- w1 fixes akar.py this season; the corpus row s18/w1-h6-loop.py is
  the repro that will flip

## Task
1. Pre-fix: capture the repro's red (the 1/20 race, the gate logs'
   verbatim shape) into tests/test_s91_w2_pins.py (_s91w2_ prefix) —
   a pin that asserts the all-pass signature, expected RED until w1's
   fix lands. The barrier harness tuned for determinism (the contract
   unchanged).
2. Post-fix (after w1 lands): the pin flips green — verify, and keep
   both colors recorded in the pins file's history (the docstring:
   red at N/20 before, 0/20 after, the commit shas).
3. The pins file also holds the corpus row's contract: the other four
   repros stay green (the s49 pin's five, minus the h6 row now pinned
   directly).
4. notes.md REQUIRED: the red capture, the green flip, the commit
   shas, the issue #17 comment (posted, one live call, disclosed).

## Bounds
- Edits: tests/test_s91_w2_pins.py. akar.py is w1's lane. One live gh
  comment on issue #17 (the red/green story), disclosed. notes.md
  REQUIRED.
