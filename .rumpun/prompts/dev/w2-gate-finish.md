# s18 w2 — land H4 containment; pin H1/H4/H6 + warning fix spec-first

You are w2 in season s18 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/lint.py, akar record
codex-review-2026-09-14 (H1/H4/H6), and the s17 salvage test draft
.rumpun/akar/evidence/s17/w2-test_rumpun.py (223 additions-only lines, 71
test functions, from the season the budget killed — audit and reuse it).
You own lint.py + the test file; w1 owns engine.py/akar.py. FILE TOOLS
directly; no nested-heredoc scripts. You have 40 minutes.

## Deliverables (write ONLY inside your workspace; the harness merges)

1. lint.py patched copy + tests/test_rumpun.py + notes.md.

## H4 — benih name containment in lint.py

Names: nonempty, 1-32 chars, [a-z0-9][a-z0-9_-]*, no "/" "\\" "..",
reserved "_season" rejected, errors name the offending benih. Seasons
s1-s17 (w1/w2/w3) must still pass.

## Spec-first tests (pin H1, H4, H6, and the warning fix)

Reuse/rework the s17 draft; the contract it pins is unchanged, plus:
- warning-transition: a synthetic stream with multiple file-tool sightings
  produces exactly ONE rumpun.engine WARNING (caplog count).
- H1 stop-race, H4 name shapes, H6 same-id append races: as in the s17
  draft (barrier-synced, no wall-clock dependence).

## Constraints

- tests additions-only vs the current repo file (70 tests kept).
- lint.py patch as a workspace copy + notes.md anchors (harness merges).
- logging, never print; ruff clean (line-length 100); py3.10+.

## Verify before finishing

Expected red set measured against current code in notes.md; the 70
existing tests green; your lint.py copy passing your H4 tests in a
scratch tree.
