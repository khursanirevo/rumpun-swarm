# s29 w1 — one collision-free mapping for discovery links and pages

You are w1 in season s29 (repo root: the parent of this .rumpun tree). Read
src/rumpun/report.py (render_discoveries + the slug rule + the s25-era
filename sanitize), tests/test_rumpun.py (the discoveries pins), and akar
record codex-review-2026-09-14 (finding L1) + s28-harvest (L1 confirmed
open on main). FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Deliverable: render_discoveries uses one mapping for both hrefs and files

Fix in report.py (workspace copy):
- one function `_discovery_filename(rid) -> str` used by BOTH the link
  builder and the page writer;
- slug rule stays (lowercase, [^a-z0-9-] to "-"), plus a deterministic
  collision suffix when two distinct ids slugify identically (e.g. the
  full original id's stable short hash appended before .html);
- the list page, the record pages, and the LANDING page's Discoveries
  card (render_index) all call the same function - one mapping, three
  call sites;
- existing lowercase ids' pages and links stay byte-identical (no hash
  suffix unless a collision actually exists in the rendered set).

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch audit.py, engine.py, harvest.py, evolve.py, cli.py,
  tests/ (w2 owns the pins; the harness merges).
- The discoveries pins (s21 batch) and the suite stay green.

## Verify before finishing

Repros: ids "Audit-1" (uppercase), "my_id" (underscore), "a.b" (dot) each
render a page their list link resolves to; ids "a-b" and "a.b" (same
slug) render two distinct pages; the real ledger's matrix re-renders
byte-identical to current output (all current ids are already clean).
Suite green against patched copies. All in notes.md.
