# s122 w2 — the close check survives bare environments (issues #39 and #40)

Two filed defects on the same seam: the close check dies on
environments it should name.

## Ground truth (measured 2026-09-20)
- issue #39: the import probe refuses exit 2 when the extract has no
  src/ - a pin-bearing season in a docs-only repo can never pass its
  pins lane.
- issue #40: the venv python falls back to sys.executable with no
  pytest probe - the pins lane dies "No module named pytest" exit 1
  on green trees.
- the checker: tools/artifact_check.py (the import probe and the
  venv python resolution)
- the house style: the named skip (the s63 false positive, the s115
  no-design convention) - name what the environment lacks, never
  crash on it; a refusal that reads as tamper is a defect
- fixture discipline: fixture trees in tmp; never copy .rumpun/runs/

## Task
1. Fix both: an extract with no src/ gets the named pins-lane skip
   (distinct from any tamper refusal); the venv python fallback probes
   pytest importability before use - a python without pytest is
   refused with the named line, never silently used. Repos with src/
   and a real venv are byte-unchanged. Pins red-first in
   tests/test_s122_closecheck_envs.py (fixture trees in tmp).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tools/artifact_check.py,
  tests/test_s122_closecheck_envs.py only. notes.md REQUIRED.
