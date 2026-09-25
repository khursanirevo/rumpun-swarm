# s80 w2 — issue #5: the deep residual, scoped honestly

"Recorded verdicts do not establish implementation correctness" — the
epistemics residual. You cannot FIX epistemology in a season; you can
scope what would count. Your deliverable: the design + its first pin.

## Ground truth
- issue #5 on khursanirevo/rumpun (open); the panel exists
  (panel-s70-verdict WIN) and shows on the board
- the campaign's own honesty markers: the check (VERIFIED), the
  harvest (band-clause claims), the panel (a second opinion) — none
  run the shipped code against the ISSUE it claims to resolve
- the s79 fix is the first case where the issue's own repro scripts
  existed: repro red -> fix -> green is the strongest closure shape
  the campaign has

## Task (spec-first, pins in tests/test_s80_w2_pins.py, _s80w2_ prefix)
1. Design the "repro-backed closure" contract: a season resolving a
   filed defect MUST carry the issue's repro (or state why none
   exists) as a pins-file test; the harvest's implies cites the
   repro's red-before/green-after. Distill into
   priors/templates/repro-backed-closure.md in the kancil-base pack.
2. Pin the contract's checkable surface: a fixture season whose pins
   carry the repro test resolves; one without is flagged by
   panel.claim_set as `repro: absent` in the review text.
3. File the contract as a comment on issue #5 (the argv builders;
   one live call, disclosed in notes) — the issue stays OPEN: the
   residual is a standing standard, not a defect. board --map s80.
4. notes.md REQUIRED: the design, the pin map, the comment url.

## Bounds
- Edits: the pack draft dir, src/rumpun/panel.py (claim_set only),
  tests/. notes.md REQUIRED. Issue #5 never closes in this season.
