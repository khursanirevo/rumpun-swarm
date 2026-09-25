# s90 w1 — the decade-8 audit + the s84 fix's first live test

Two real jobs: the decade audit is due at this boundary, and the s84
composer fix (reading the resolution trail) has never been tested on
the data that motivated it.

## Ground truth (measured 2026-09-17)
- audit-44 re-emitted audit-43's resolved residuals verbatim (issue
  #6, filed and closed); the s84 fix makes the composer read the
  resolution trail (issues #3/#4 closed citing the lines; the harvest
  records name them)
- the decade audits: audit-43 (s80's boundary), audit-44 (s89's...
  recorded 2026-09-17), audit-45 = this boundary's run
- the composer: src/rumpun/audit.py (the s84 trail check)

## Task
1. Run the decade-8 audit: `rumpun audit --last 10` (the verb's own
   path, which now carries the s84 trail check). Record audit-45's
   candidate lines.
2. THE LIVE TEST: audit-43/44's three resolved residual lines must
   NOT re-emerge as candidates (they may appear as resolved: markers
   per the landed shape). If they re-emerge as candidates, the s84
   fix has a live hole — file it as a precise new issue with the
   audit-45 record as evidence.
3. Any NEW candidates (not in the trail): file as board issues
   (one per candidate, item-add to project 1).
4. notes.md REQUIRED: audit-45's candidate/resolved lines, the
   re-emergence verdict, any new issue urls.

## Bounds
- The audit verb's own path only; no direct composer edits. notes.md
  REQUIRED. One audit run.
