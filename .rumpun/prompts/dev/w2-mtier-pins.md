# s21 w2 — L2 barrier in the dual-start test + M3/M11 pins

You are w2 in season s21 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, tests/test_rumpun.py (the dual-start test),
src/rumpun/harvest.py, src/rumpun/routes.py, akar record
codex-review-2026-09-14 (M3, M11, L2). You own tests/; w1 owns harvest.py
and routes.py. FILE TOOLS directly. 40 minutes.

## L2 — give the dual-start test its barrier

Today both starters are Poped back-to-back and contention is luck (~1/5
loaded runs let starter 2 miss the race and exit nonzero; 5+ transients
observed, review L2). Fix per the review: hold starter 1 INSIDE the spawn
transaction with an explicit barrier, then release it after confirming
starter 2 is contending. A deterministic shape: a fake route command that
blocks on a marker file (slow-start stub), starter 2 launched while
starter 1 demonstrably holds the flock (its spawned-alphas line not yet
emitted), then release. Keep every existing assertion (single spawn,
completed, exit 0 both). The test must pass 5 consecutive runs.

## Spec-first pins (M3 + M11, red against current code)

- M3: after harvest_season(...) on a scratch WIN season,
  rimba/<sid>/verdicts.jsonl carries the season-level WIN row; report
  renders WIN; a second harvest refuses (M4 minimal form).
- M11: every command write_routes generates contains no "<model>"
  placeholder and passes /bin/sh -n; scaffold output matches.

## Constraints

- tests additions-only vs the current repo file (99 tests kept) plus the
  dual-start barrier edit (in-place modification of THAT test only).
- logging, never print; ruff clean (line-length 100); py3.10+.

## Verify before finishing

Measured red set against current code in notes.md; the 99 existing tests
green; dual-start 5 consecutive green runs in a scratch tree.
