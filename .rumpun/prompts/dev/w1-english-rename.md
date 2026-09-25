# s45 w1 — the path and state renames with back-compat aliases

You are w1 in season s45 (repo root: the parent of this .rumpun tree). Read
src/rumpun/engine.py, src/rumpun/report.py, src/rumpun/audit.py,
src/rumpun/harvest.py, src/rumpun/evolve.py, src/rumpun/lint.py, and the
operator's rename confirmation (the direct ledger). FILE TOOLS directly.
WRITE ONLY inside your workspace. 40 minutes.

## The renames (old -> new, aliases accepted)

- musim/ -> seasons/ (the seasons directory; engine season_count,
  _season_ids, evolve draft scanning, audit liveness)
- akar/ -> ledger/ (the evidence ledger directory; harvest, audit,
  evolve, the usefulness runner's evidence scan)
- rimba/ -> runs/ (the run tree; engine season_dir, report paths)
- akar.AkarError stays (the exception class is code, not surface)
- state_path/season_dir helpers: one place each, updated once

## Deliverable: every module above resolves the new names, with
old-name aliases accepted at the READ boundaries

The rule: WRITES use the new names only (a fresh init never creates the
old ones); READS accept both (a historical season rooted at musim/ or
akar/ still resolves - the 45 historical seasons keep their records).
Implement a small path-resolution helper per renamed directory
(e.g. seasons_dir(root) returns seasons/ if present else musim/), so
the alias logic lives in exactly one place per directory. The citation
PREFIX rename (akar: -> ledger:) is w2's; your reads must accept both
prefixes where the audit/lint parse them.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch lint.py's yaml keys (w2), cli.py, tools/, tests/.
- The 188-test suite stays green (the suite uses fixture paths - update
  ONLY if a fixture writes old-name dirs that nothing aliases; report
  any such case).

## Verify before finishing

Repros: a fixture tree built with OLD names resolves through harvest,
audit, report, evolve, season_count; the same tree with NEW names
resolves identically; a fresh init produces no old-name directories.
Suite green against patched copies. All in notes.md.
