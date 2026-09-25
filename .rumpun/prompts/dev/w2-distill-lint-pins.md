# s83 w2 — the distill-lint contract, pinned from the other side

w1 fixes the placement (distill runs the content lint). Your slice:
the adversarial pins — the shapes that must never seal again.

## Ground truth (measured 2026-09-17)
- issue #10: the kancil-base draft sealed at s67/s77/s80 with zero
  findings while carrying `/error-exp` in a code span (ABS_PATH_RE,
  plugin.py:79); the s81 install gate was the first lint pass
- w1 lands: distill runs the content lint before sealing; the refusal
  (or recorded-findings) shape is theirs; your pins hold the
  never-again contract from the outside

## Task (spec-first, pins in tests/test_s83_w2_pins.py, _s83w2_ prefix)
1. Adversarial seal pins over fixture packs: a priors file carrying a
   slash-led token in a code span, an absolute path in plain text, a
   parent-relative escape (`../`) — NONE may seal silently; each
   either refuses or records the finding in the manifest, per w1's
   landed shape (pin the landed shape, whatever it is, and assert it
   is not silent).
2. Pin the digest invariant: the sealed manifest's digest equals a
   fresh recompute over the sealed priors (the s81 three-way
   convention), including after a refused-then-fixed re-seal.
3. Pin the install gate's agreement: for the same fixture pack,
   distill's accept/reject decision matches install's (the two gates
   cannot disagree again).

## Bounds
- Edits: tests/ only (w1 owns plugin.py). notes.md REQUIRED. No live
  route call, no real pack mutation.
