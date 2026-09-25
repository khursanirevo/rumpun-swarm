# s17 w2 — benih name containment (H4) + spec-first tests for H1/H4/H6

You are w2 in season s17 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/lint.py, src/rumpun/engine.py, src/
rumpun/akar.py, and akar record codex-review-2026-09-14 (your scope: H4
implementation + spec-first tests for H1, H4, H6). You own lint.py; w1 owns
engine.py and akar.py. Use your FILE TOOLS; no nested-heredoc scripts.

## H4 — benih name containment in lint.py

Today: lint checks duplicate names but accepts "../../outside" and
"_season"; the engine joins names onto the season dir, so traversal
escapes the season and _season overwrites harness state.
Fix in lint.py: names must be nonempty, 1-32 chars, [a-z0-9][a-z0-9_-]*,
must not equal reserved names ("_season"), must not contain "/" or "\\" or
"..", and must not resolve (symlink-safe check is engine-side later; lint
rejects the shapes). Error messages name the offending benih. Existing
valid seasons (s1-s17 use w1/w2/w3) must still pass lint.

## Spec-first tests (pin all three fixes; expected red against current code)

1. H1: a stop racing a spawn — slow stub route, stop_season from a thread
   mid-spawn — the final state contains every spawned name and no live
   untracked process remains (use a marker file the stub writes to prove
   it was terminated or never admitted; do not require wall-clock timing).
2. H4: lint rejects "../../x", "_season", "a/b", "", ".hidden", 33-char
   names; accepts "w1", "alpha-1", "w2_x"; the error names the benih.
3. H6: two threads under a barrier calling akar.append_record with the
   same id — exactly one succeeds, the other raises AkarError, the file's
   body matches the winner, and the record count is 1.
4. Regression: the full existing suite stays green; lint error output
   format unchanged for existing cases.

## Constraints

- tests/test_rumpun.py based on the current repo file (70 tests kept;
  additions + minimal helpers only — diff must be additions-only).
- lint.py patch applied to a copy in this workspace + notes.md anchors
  (harness merges).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Never log token values.

## Verify before finishing

Expected red set in notes.md (measured), suite green for the 70 existing
tests against current code, and your lint.py copy passing your new H4
tests in a scratch tree.
