# s119 w2 — the board mirrors the ledger on demand

The board IS the backlog, and the ledger holds the verdicts; the two
drift apart on every close. The sync makes one command true them up.

## Ground truth (measured 2026-09-20)
- the surfaces: src/rumpun/board.py and src/rumpun/kanban.py (the
  gh-backed board verbs; the gh project CLI prints TSV without --json)
- the truth: runs/<sid>/verdicts.jsonl rows and the harvest records -
  the same sources the epics rollup reads
- the s66 lesson: board cards legitimately name other machines'
  seasons; the sync mirrors the LOCAL ledger, never censors foreign
  rows
- fixture discipline: no network in pins; the gh surface rides a
  seam or the pins test the pure mirror logic over fixture verdicts

## Task
1. Land the sync: one verb (or flag) mirrors the ledger verdicts to
   the board cards on demand - new cards for seasons with no card,
   updated bodies for drifted ones, nothing invented, idempotent (a
   second run changes nothing). Pins red-first in
   tests/test_s119_board_sync.py (the pure mirror logic over fixture
   verdicts; no network).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/board.py, src/rumpun/kanban.py, src/rumpun/cli.py
  (the board verb only), tests/test_s119_board_sync.py only.
  notes.md REQUIRED.
