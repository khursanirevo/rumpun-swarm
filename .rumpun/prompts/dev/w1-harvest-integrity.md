# s40 w1 — harvest integrity: M4 full + write-order repair

You are w1 in season s40 (repo root: the parent of this .rumpun tree). Read
src/rumpun/harvest.py (harvest_season), src/rumpun/engine.py
(read_persisted_status), and akar records audit-29 + s29-harvest. Context:
s32's live instance - the verb wrote the verdicts row, then the akar
append never landed, stranding the row (repaired by hand, noted in the
s32-harvest record). FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Deliverables (src/rumpun/harvest.py, workspace copy)

1. M4 full: harvest_season refuses a season whose persisted status is not
   terminal (completed / stopped_* / failed): AkarError naming the season
   and its status. Only terminal seasons harvest - the permanent id is
   never consumed by a partial judgment. (The s21 row-exists refusal
   stays as the second guard.)
2. Write order: the akar record is appended BEFORE the verdicts.jsonl
   season row. A failure after the akar append but before the row write
   leaves the record as the recovery source (the row can be re-added);
   a failure before the akar append strands nothing.
3. Both changes inside harvest_season; callers unchanged (cli passes the
   same arguments; the s24 --band/--observed flags keep working).

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch audit.py, engine.py, evolve.py, lint.py, collab.py,
  cli.py, report.py, tests/ (w2 owns the pins; the harness merges).
- The 185-test suite stays green.

## Verify before finishing

Repros: (1) harvest of a running-season fixture raises AkarError naming
season + status, with no id consumed and no row written; (2) an injected
akar fault between the appends leaves no verdicts row; (3) a terminal
season with its row present still refuses (the s21 regression pin).
Suite green against patched copies. All in notes.md.
