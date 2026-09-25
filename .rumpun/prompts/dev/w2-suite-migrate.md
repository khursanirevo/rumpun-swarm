# s47 w2 — the test suite's migration to the new layout

You are w2 in season s47 (repo root: the parent of this .rumpun tree). Read
tests/test_rumpun.py (the 12 fixture-path reds), the s45 rename's
GLOSSARY.md, and akar record audit-35. You own tests/. FILE TOOLS
directly. WRITE ONLY inside your workspace. 40 minutes.

## Deliverable: the 12 fixture-path reds reconciled

The 12 failing tests' fixtures build the OLD layout (.rumpun/musim,
.rumpun/akar, .rumpun/rimba) while the renamed code resolves the NEW
names first. Fix: the fixtures build the NEW layout (seasons/, ledger/,
runs/) — the tests then exercise the migrated code's real paths. The
alias pins (old-name fixtures resolving through the fallback) stay as
they are — they pin the fallback honestly.

The 12 (the current -rf list): dual_start, watch_cycle,
stop_racing, engine_spawns_inside_workspace_cwd,
rollback_active_season_stops_agents_before_record,
agent_budget_deadline_is_per_agent, season_all_agents_failed,
draft_after_rejecting_latest, audit_without_matrix_byte_identical,
audit_without_corpus_flag_byte_identical, the two draft goldens.

## Constraints

- The fixtures' SEASON yamls keep their benih key: the engine accepts
  both (the writer-table alias) — do not rename the yamls' keys, only
  the directory layout.
- tests additions-only where new pins are added; the 12's own fixture
  edits are in-place.
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns the code.

## Verify before finishing

The 12 green against the migrated fixtures; the 171+ suite green.
Both in notes.md.
