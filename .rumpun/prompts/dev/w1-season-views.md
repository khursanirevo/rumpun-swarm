# s115 w1 — the season views stop guessing (issues #31 and #35)

Two filed defects, one surface pair. The resolve-all directive (seq 16)
reads the fresh filings.

## Ground truth (measured 2026-09-20)
- issue #31: the season list row order flipped (newest last -> first);
  consumers must not guess. The verb: cmd_season_list
  (src/rumpun/cli.py:371).
- issue #35: season status errors on a drafted-only season that the
  list renders as no state. The verb: cmd_season_status
  (src/rumpun/cli.py:307); the engine side raises
  "no season state for '<sid>'" (src/rumpun/engine.py, the
  read_persisted_status block around line 1297).
- a drafted-only season: the yaml exists under .rumpun/seasons/ but no
  run state exists under .rumpun/runs/<sid>/ - the apply without the
  start, a real state in this campaign (s109-s115 all drafted before
  their start).
- the resolve-all convention: the fix commit message names the issue
  numbers; the issues close after the close check verifies the season.

## Task
1. Fix both: the list renders newest-first with the order named in its
   help text; the status verb renders a drafted-only season as the
   named no-state shape instead of erroring. Pins red-first in
   tests/test_s115_season_views.py (the s108 fixture pattern:
   real yamls, no network; synthesize drafted-only state in tmp).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/cli.py (the two season verbs), src/rumpun/engine.py
  (only if the status fix needs it), tests/test_s115_season_views.py
  only. notes.md REQUIRED.
