# s23 w1 — M2 declared-artifact liveness + M8 id high-water mark

You are w1 in season s23 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/audit.py, src/rumpun/evolve.py, akar
record codex-review-2026-09-14 (M2 + M8 with reproductions). FILE TOOLS
directly. WRITE ONLY inside your workspace. 40 minutes.

## M2 — liveness checks declared artifacts directly

Today _season_artifacts intersects a fixed LEDGER_ARTIFACTS list, so a
declared `writes: custom.jsonl` present in every season counts as absent —
false dead-phase candidates (reviewer reproduced). Fix: for each declared
phase, check its OWN writes filename in each audited season dir (existence
of that exact file), and count the denominator as completed seasons whose
own yaml declared that phase. The F1 line keeps its shape; false
candidates disappear. audit's existing tests (s13 batch) must stay green.

## M8 — draft ids from a lifecycle high-water mark

Today draft numbering scans only top-level musim/s*.yaml: reject the
latest season and the next draft reuses its id, colliding with approval
records (reviewer reproduced). Fix: the next id derives from a persistent
high-water mark = max over musim/s*.yaml AND musim/rejected/* AND any
akar lifecycle records (reject-/rollback-<sid> patterns) — or a dedicated
counter file; pick one mechanism, document it. Apply/lint of a reused id
against an existing reject record already refuses (s20 H8) — this closes
the generation side.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch lint.py, collab.py, engine.py, cli.py, report.py, tests/
  (w2 owns the test pins; the harness merges).
- Existing F1-F6 line shapes and candidate triggers stay compatible
  (s13's pins must stay green).

## Verify before finishing

Repros: a two-season fixture declaring writes: custom.jsonl present in
both yields NO dead-phase candidate and an F1 line counting 2-of-2; a
completed-only denominator ignores a pre-phase season; reject the latest
season then draft — the new id skips the rejected one. Suite green
against patched copies. All in notes.md.
