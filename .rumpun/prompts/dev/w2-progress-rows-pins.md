# s24 w2 — spec-first pins for content-based progress + harvest row fields

You are w2 in season s24 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/engine.py (the progress check),
src/rumpun/harvest.py, src/rumpun/cli.py (the harvest verb), akar records
stall-rule-fired-on-runtime + audit-12. You own tests/; w1 owns the
implementations. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Spec-first pins (red against current code)

1. Content-based progress: two stubs, same elapsed wall time past the
   stall window — the one whose log GREW by appended bytes is running;
   the one whose log was only TOUCHED (mtime bumped, size unchanged) is
   stalled. No wall-clock-dependent asserts beyond the existing pattern.
2. The M10 trade-off comment references the content-based rule (grep the
   engine source in the pin via inspect — the decision text moved).
3. Harvest rows: harvest_season with band/observed writes a season row
   carrying both non-empty; the cli verb with --band/--observed passes
   them through; without the flags both stay "".
4. Regression: the 117-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (117 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns the implementations.

## Verify before finishing

Measured red set against current code in notes.md; the 117 existing
tests green; the pins' behavior documented test by test.
