# s123 w1 — the lane-commit rule codified, the loop draft preferred

Three writer commits happened before anyone wrote the rule down. The
rule lands in the operator surfaces, and the planner prefers the
loop's draft when one exists.

## Ground truth (measured 2026-09-20)
- the incidents: s114 w2 committed 78ed003, s122 w1 committed ef4a78d
  - both exactly their bounded files, both season-tagged subjects
- the planner: src/rumpun/evolve.py draft (the s116 warning pattern
  is the house style); the loop's drafts land at
  runs/<parent>/seasons/<next>.yaml (the s120/s122 machinery)
- the operator surfaces: docs/campaign-guide.md (the close section),
  the README's lifecycle section
- fixture discipline: tmp campaigns; the real ledger never written
  in tests

## Task
1. Codify: the campaign guide and the readme lifecycle section state
   the lane-commit rule (a writer may commit exactly its bounded
   files, subject <= 50 chars, season-tagged; the close worker folds
   the rest). The planner warns at plan time when the loop's draft
   exists for the next id (naming its path) - the worker fills that
   draft instead of a fresh one. Pins red-first in
   tests/test_s123_commit_convention.py.
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/evolve.py, docs/campaign-guide.md, README.md,
  tests/test_s123_commit_convention.py only. notes.md REQUIRED.
