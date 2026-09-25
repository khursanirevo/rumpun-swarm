# s20 w2 — H8 rejected/rejected-rollback lifecycle + pins for H5/H8/H9

You are w2 in season s20 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/evolve.py, src/rumpun/engine.py (the
start + stop paths), akar record codex-review-2026-09-14 (H8 + the H5/H9
reproductions), and s18/s19 evidence for the repro-first pattern. You own
evolve.py; w1 owns engine.py. FILE TOOLS directly. 40 minutes.

## H8 — rejected seasons are non-executable; rollback coordinates

Today: rejection moves yaml into musim/rejected/ but nothing checks
placement — a rejected file lints and starts (reviewer reproduced);
rollback records containment without stopping an active season. Fix:
1. evolve.apply (or the apply path's final gate) refuses a season id that
   has a reject-<sid> record (scan akar/ the same way citations resolve).
2. season start refuses a season whose yaml sits outside musim/ canonical
   placement (rejected/ or drafts): resolve the yaml path and require the
   parent dir to be musim/ (drafts apply via evolve, not start).
3. rollback_season stops an ACTIVE season first (reuse engine.stop_season),
   then records containment — ordered, not concurrent.

## Spec-first tests (pin H5, H8, H9 against w1's patch)

- H5: mid-spawn route failure → both the error recorded AND no live
  untracked child (marker-file stub, no wall-clock waits).
- H9: short-budget agent terminated at its own deadline while the
  long-budget sibling completes (seconds-scale stubs).
- H8: rejected season start raises; rejected season apply refuses;
  rollback of an active season stops it before recording.
- Regression: the 94-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (94 tests kept).
- evolve.py patch as a workspace copy + notes.md anchors (harness merges).
- logging, never print; ruff clean (line-length 100); py3.10+.

## Verify before finishing

Measured red set against current code in notes.md; 94 existing tests
green; your evolve.py copy passing your H8 tests in a scratch tree.
