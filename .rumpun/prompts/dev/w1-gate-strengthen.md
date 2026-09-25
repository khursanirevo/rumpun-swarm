# s43 w1 — reachable-artifact falsify + DRIFT mismatch arming

You are w1 in season s43 (repo root: the parent of this .rumpun tree). Read
src/rumpun/lint.py (the s34 falsify gate), src/rumpun/audit.py (the s35
mismatch arming + the corpus candidate block), and akar records audit-32 +
usefulness-decade-4 (residuals 7 and 8, confirmed by the triage). FILE
TOOLS directly. WRITE ONLY inside your workspace. 40 minutes.

## Deliverable 1: reachable-artifact falsify (lint.py)

Today: the falsify gate accepts any phase with a non-empty reads —
reading a foreign file satisfies falsification. Strengthen: the reading
phase's artifact must be PRODUCED within the declared pipeline (some
other phase's writes names it — a reachability check over the
pipeline's writes set). A season whose only reader reads an artifact
nothing writes errors, naming the season and the unreachable artifact.

## Deliverable 2: DRIFT mismatch arming (audit.py)

Today: the mismatch arming counts only FAIL rows; a DRIFT corpus row
(a script's assumptions moved) escapes — the reviewer's own probe.
Strengthen: a DRIFT row arms a mismatch candidate citing the drifted
script and its note (same shape as the FAIL mismatch: one candidate per
drifted script, before the cap). The corpus regression candidate
(FAIL/REGRESSION) keeps its priority ahead of improvements.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch collab.py, engine.py, harvest.py, evolve.py, cli.py,
  report.py, tools/, tests/ (w2 owns the pins; the harness merges).
- The 171-test suite stays green (the s34 falsify pins adjust only if
  their fixtures read unreachable artifacts — fix the fixtures to the
  reachable shape, documented).

## Verify before finishing

Repros: a season whose only reader reads an unwritten artifact errors
naming both; a reachable reader passes; a DRIFT matrix row arms a
candidate citing the script. Suite green against patched copies (the
s34 falsify fixtures updated to the reachable shape). All in notes.md.
