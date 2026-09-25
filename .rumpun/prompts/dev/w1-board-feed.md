# s76 w1 — feed the board from the audit, close the first issue

The board exists (project 1) and the lifecycle is wired. Your lane:
turn audit-43's residual candidates into board issues, then close the
campaign's oldest open loop.

## Ground truth (measured 2026-09-17)
- board: project 1 (rumpun), issue #1 the one item; pickup verified
- audit-43 (2026-09-17): three usefulness-decade-1 residual candidates
  in .rumpun/ledger/2026-09-17_audit-43.md (candidate: lines)
- panel-s70-verdict sealed WIN; s75 landed the panel's teeth
- board.py: issue_create_argv, item_add_argv, sync_season, the live
  seam; rumpun board --sync <sid> [--dry-run]

## Task
1. Read audit-43's candidate lines. File each as a board issue on
   khursanirevo/rumpun (title = a compressed form of the candidate;
   body = the candidate verbatim + the audit-43 citation). item-add
   each to project 1.
2. Close issue #1 honestly: `rumpun board --sync s75 --dry-run` first
   (read the render), then the real sync. Issue #1 asked for panel
   tooling; the panel exists, spoke (panel-s70-verdict), and shows on
   the board — the issue's ask is met. The sync comments the sealed
   record and closes it. If the sync's map/lanes cannot find issue #1
   for s75's lanes, comment+close via the argv builders directly and
   record the gap in notes.md (the map wiring becomes s77 scope).
3. Verify live: `gh issue list -R khursanirevo/rumpun --state all`;
   the board item list reflects the closure.
4. notes.md REQUIRED: every issue number/url, the sync output, the
   final board state.

## Bounds
- No board.py edits unless the sync fails structurally (record it).
- One pass; no retries beyond a single re-run of a failed command.
