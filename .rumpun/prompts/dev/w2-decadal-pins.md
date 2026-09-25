# s33 w2 — spec-first pins for the decadal usefulness audit

You are w2 in season s33 (repo root: the parent of this .rumpun tree). Read
src/rumpun/audit.py, tools/replay_corpus.py (the runner pattern), akar
records codex-usefulness-2026-09-15 + audit-19. You own tests/; w1 owns
audit.py + tools/. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Spec-first pins (red against current code)

1. Decade trigger: a 10-season fixture ledger arms the "usefulness audit
   due for decade 1" finding; a 9-season ledger does not; an existing
   usefulness-decade-1 record suppresses it.
2. Runner: with a stub different-model route, tools/usefulness_audit.py
   appends a usefulness-decade-N akar record carrying the parsed verdict
   line; the captured route output does not land in the record.
3. Honesty: a route exiting nonzero, timing out, or omitting the verdict
   line raises honestly (nonzero + named reason); no record is appended.
4. Residual arming: a verdict record's residuals arm candidates through
   the existing candidate machinery (fixture: a usefulness record with
   residual lines -> candidates cite them).
5. Regression: the 150-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (150 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ or tools/ — w1 owns them.

## Verify before finishing

Measured red set against current code in notes.md; the 150 existing
tests green.
