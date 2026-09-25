# s54 w1 — the rename finished: schema keys to English

You are w1 in season s54 (repo root: the parent of this .rumpun tree).
Read src/rumpun/lint.py, src/rumpun/engine.py (draft_next and the benih
roster reader), src/rumpun/cli.py (the tuai help string, the musim/
message strings), the newest operator directive (ledger directives), and
akar records s53-harvest + audit-38. FILE TOOLS directly. WRITE ONLY
inside your workspace EXCEPT minimal documented code changes. 40
minutes.

## Deliverables (workspace copies; the harness merges)

1. The season yaml schema key `benih:` becomes `writers:`: lint.py and
   engine.py read `writers:` first and `benih:` as back-compat; draft_next
   emits `writers:` in new drafts.
2. cli.py: the harvest help "tuai: close a season into akar" becomes
   English; the `musim/rejected/` message strings in evolve reject and
   rollback state the real paths (.rumpun/seasons/rejected/). The word
   "akar" leaves user-facing strings (records are "ledger records").
3. Workspace trees stay rimba/ if gitignored-only, or rename to
   workspaces/ with the engine paths updated - w1 decides by the
   smallest diff and records the choice in notes.md.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- The suite floor holds; historical yamls and DESIGN entries stay as written.
4. Found live (2026-09-16): the `direct` verb writes operator directives
   to the pre-rename path .rumpun/akar/directives.jsonl while the
   campaign's real history is .rumpun/ledger/directives.jsonl. Fix the
   path to ledger/, keep one seq numbering (max seq + 1), and migrate
   the stray record so the audit reads it.

## Scope correction (2026-09-16, operator: focus on the rename)
- Deliverable 3 is stale: the rimba/ DIRECTORY is already gone (runs live
  under .rumpun/runs/). The real leftovers are STRING references: the F1
  phase-liveness text "rimba/<sid>/" in audit.py, cli.py's
  _serve_rimba helper + the `season report --serve` help, lint.py:45's
  comment. Sweep them to English (serve_runs, "runs tree").
- New evidence citations prefer `ledger:` (the glossary keeps `akar:`
  resolving as the read alias). The akar.py module name stays: internal
  symbol, aliased per the glossary, not operator-facing surface.
