# s126 w1 — models --write re-reads a filled campaign

The route catalog landed; the detection verb still refuses a filled
campaign - the s125 w2 lane named the refusal as its finding.

## Ground truth (measured 2026-09-20)
- the verb: rumpun models [--write] (wrote 9 routes at the s121 live
  init; the refusal on a filled campaign is the s125 w2 finding)
- the truth it must respect: a filled routes block in
  .rumpun/rumpun.yaml carries hand-tuned templates (the glm route
  moved to 5.3 by probe at s125) - a redetect must never clobber them
- the shape: diff the detected routes against the config, write only
  named additions, print what changed, stay idempotent (a second run
  writes nothing)
- fixture discipline: tmp campaigns; the real rumpun.yaml never
  written in tests

## Task
1. Land the re-detect: models --write on a filled campaign writes only
   the newly detected route keys (existing lines byte-untouched),
   prints the diff, and is idempotent. Pins red-first in
   tests/test_s126_models_redetect.py (tmp campaigns).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: the models verb's module, tests/test_s126_models_redetect.py
  only. notes.md REQUIRED.
