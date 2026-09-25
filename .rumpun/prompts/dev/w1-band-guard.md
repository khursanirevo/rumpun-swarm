# s32 w1 — the band-mask lint guard + recalibrate-candidate retirement

You are w1 in season s32 (repo root: the parent of this .rumpun tree). Read
src/rumpun/lint.py, src/rumpun/audit.py (the recalibrate candidate), akar
records audit-20, audit-19, and the s12/s17-era harvest records (the
masking evidence: LOSS seasons whose bands never defined integration).
FILE TOOLS directly. WRITE ONLY inside your workspace. 40 minutes.

## Deliverable 1: the band-mask lint guard (lint.py)

A WARNING (never an error) when a season yaml:
- declares metric modules_integrated (exact match), AND
- its methodology.primary_change.expected_band text contains none of the
  integration-evidence tokens (case-insensitive): "integration",
  "integrated", "suite", "tests".
The warning names the season id. All existing seasons' yamls must pass
without NEW warnings (verify: s17-s31 bands all carry the tokens; s5-s12
yamls are historical and may warn — check and report).

## Deliverable 2: recalibrate-candidate retirement (audit.py)

The recalibrate candidate fires only when the warned set is non-empty in
the audited window: compliant bands stop arming it. Keep the F-line
shape; the candidate's trigger gains the guard's warned-seasons set.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch collab.py, engine.py, harvest.py, evolve.py, cli.py,
  report.py, tools/, tests/ (w2 owns the pins; the harness merges).
- The 145-test suite stays green.

## Verify before finishing

Repros: a modules_integrated season with a non-integration band warns;
the same season with "the suite is green and 2 modules integrated"
stays silent; the s17-s31 season yamls produce zero new warnings
(count before/after). Suite green against patched copies. All in notes.md.
