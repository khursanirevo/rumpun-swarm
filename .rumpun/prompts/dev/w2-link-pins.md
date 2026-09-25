# s29 w2 — pins for the discovery-link mapping

You are w2 in season s29 (repo root: the parent of this .rumpun tree). Read
src/rumpun/report.py (render_discoveries), akar record codex-review-2026-09-14
(L1) + s28-harvest (L1 confirmed open). You own tests/; w1 owns report.py.
FILE TOOLS directly. WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. Uppercase id: a record "Audit-1" renders a page and the list link
   resolves to that existing page (path exists after render).
2. Underscore id: "my_id" same contract.
3. Dot id: "a.b" same contract.
4. Collision: ids "a-b" and "a.b" (identical slugs) render TWO distinct
   pages, each link resolves, neither overwrites the other.
5. Regression: the current ledger's ids (all lowercase-hyphen) render
   byte-identical list + pages to pre-s29 output (A/B compare).
6. Regression: the 133-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (133 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns report.py.

## Verify before finishing

Measured red set against current code in notes.md; the 133 existing
tests green.
