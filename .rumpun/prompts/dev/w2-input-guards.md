# s23 w2 — M9 input guards + M10 trade-off pin + pins for M2/M8/M9

You are w2 in season s23 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/lint.py, src/rumpun/yamlio.py,
src/rumpun/engine.py (the stall rule), akar record
codex-review-2026-09-14 (M9 + M10), and s22 evidence (the repro-first
pattern). You own lint.py + yamlio.py + tests/; w1 owns audit.py and
evolve.py. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## M9 — malformed inputs fail as domain errors

Today lint records invalid methodology then calls .get on it:
`methodology: null` raises uncaught AttributeError (reviewer
reproduced). yamlio's key check skips lists, so nested non-string keys
pass its advertised contract. Fix: container-type checks before
traversal in lint (methodology/node/benih entries must be mappings —
domain error naming the path); yamlio recurses through sequences and
raises YamlError on non-string keys at any depth.

## M10 — pin the accepted trade-off

The stall rule (s15 hot-fix) accepts mtime-only progress: touching
agent.log defeats stall detection until budget. That was an accepted
trade-off (record: stall-rule-fired-on-runtime). Pin it: a code comment
on the progress check stating the accepted behavior and its limit, a
DESIGN-quoted test documenting the decision (touch-only progress keeps
the spawn running until budget), and notes.md recording the
content-based-progress candidate for a future season.

## Spec-first pins (red against current code)

- M2 (w1's patch): declared custom artifact present everywhere -> no
  dead-phase candidate; denominator counts only completed seasons
  declaring the phase.
- M8 (w1's patch): reject the latest season then draft — no id reuse.
- M9: methodology null, node as string, benih entry as list, nested
  non-string keys — all domain errors naming the path; valid docs pass.

## Constraints

- tests additions-only vs the current repo file (108 tests kept).
- lint.py + yamlio.py patches as workspace copies + notes.md anchors.
- logging, never print; ruff clean (line-length 100); py3.10+.

## Verify before finishing

Measured red set against current code in notes.md; the 108 existing
tests green; your lint.py/yamlio.py copies passing your M9 tests in a
scratch tree.
