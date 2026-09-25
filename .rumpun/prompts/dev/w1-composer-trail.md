# s84 w1 — fix issue #6: the audit reads its own resolution trail

audit-43's residuals were resolved in s80 with evidence; audit-44
re-emitted them verbatim the same day. The composer must read its own
resolution trail before re-emitting a candidate.

## Ground truth (measured 2026-09-17)
- issue #6 (OPEN): audit-44 re-emitted the same three usefulness-decade-1
  lines audit-43 carried, after s80 resolved all three
  (#3 closed stale on a fresh VERIFIED run, #4 closed on the fresh
  counts composer, #5 scoped into the repro-backed-closure standard)
- tools/usefulness_audit.py: the composer emits `candidate: ` lines
  from the audit reflection; the resolution trail lives in the board's
  closed issues (#3, #4) and the harvest records citing them
- w2 pins the contract adversarially; your fix makes it pass

## Task
1. Reproduce: run the composer over the current ledger — the resolved
   candidates re-emerge (the issue #6 evidence, in your lane).
2. Fix the smallest surface: before emitting a candidate, check its
   resolution trail — a board issue citing the candidate that is
   CLOSED, or a harvest record whose implies/observed names the
   candidate's resolution — and mark it resolved (drop it, or emit it
   as `resolved: ` instead of `candidate: `; pick per the code's
   shape and record which).
3. Pins (tests/test_s84_w1_pins.py, _s84w1_ prefix, offline): the
   resolved-candidate suppression (a fixture ledger + a fixture
   closed-issue trail), the unresolved passthrough (a fresh candidate
   still emits), and the marker you chose.
4. Verify: re-run the composer over the current ledger — audit-43's
   three lines must not re-emerge as candidates. notes.md REQUIRED.

## Bounds
- Edits: tools/usefulness_audit.py, tests/. No live gh call in pins
  (the trail is fixture-seeded). No .rumpun state edits.
