# s258 w1 — the process score

The scorer lane: grade the campaign's recent seasons against the
close protocol and brief compliance; seal the findings as pins.

## Ground truth (measured 2026-09-24)
- the corpus: the last sixteen completed seasons, enumerated from
  .rumpun/ledger at run time (re-derive the set, never copy a
  range from this brief)
- the rubric, pass/fail per season, every finding cited:
  1. harvest record exists in .rumpun/ledger
  2. DESIGN.md has a tail entry (grep the season heading)
  3. the next season yaml was seeded (.rumpun/seasons)
  4. a close commit names the season (git log)
  5. a check record exists at the close HEAD
  6. the brief's record target matches the landed record path
     (the frozen-brief drift: targets froze at s214 names)
  7. lane writes stayed inside the brief's bounds paths
  8. notes.md exists per lane, states rc plus drift-or-none
- corroborated failures to expect (verify, do not assume):
  s214-s254 closed harvest-only (no DESIGN entry, no commit, no
  push); s256 completed unclosed at draft time
- scratch scripts live in /tmp only; reads only otherwise

## Task
1. Score the corpus; seal the report as a record under tests/
   with the next free per-family process-score name (never
   overwrite a landed record); pins assert the per-season
   findings with citations embedded.
2. Verify: solo pins green; ruff clean
   (--no-respect-gitignore).
3. notes.md REQUIRED before ending the turn (rc, corpus size,
   per-rubric tallies, drift-or-none). Never wait on a background
   job at turn end.

## Bounds
- Repo edits: the one new record file only. Everything else is
  read-only.
