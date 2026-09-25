# s84 w2 — the resolution-trail contract, pinned adversarially

w1 fixes the composer to read its own resolution trail. Your slice:
the adversarial pins — a resolved candidate can never re-enter, and
the suppression cannot eat a fresh candidate.

## Ground truth (measured 2026-09-17)
- issue #6 (OPEN): audit-44 re-emitted audit-43's three resolved
  residual lines verbatim the same day s80 resolved them
- the resolution trail: the board's closed issues (#3, #4) and the
  harvest records whose implies/observed name the resolution
- w1 lands: candidates check the trail before emitting (drop, or
  `resolved: ` markers — pin the landed shape)

## Task (spec-first, pins in tests/test_s84_w2_pins.py, _s84w2_ prefix)
1. Adversarial suppression pins over fixture ledgers: a candidate
   whose resolution trail is complete NEVER re-emerges as `candidate:`;
   a candidate with NO trail (fresh) always emits; a PARTIAL trail
   (one of two citations resolved) behaves per w1's landed shape —
   pin that shape and assert it is not silent either way.
2. Pin the trail-reading contract: the closed-issue matching is
   deterministic over a fixture trail (title/body citation match),
   no live gh call.
3. Pin the composer's output shape: `candidate:` and `resolved:`
   lines are distinguishable, and the audit record's seal covers both
   (the s66-shape output contract).
4. notes.md REQUIRED: the pin map, what stayed with w1.

## Bounds
- Edits: tests/ only (w1 owns tools/usefulness_audit.py). No live gh
  call in pins. No .rumpun state edits.
