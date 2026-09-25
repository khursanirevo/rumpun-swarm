# s125 w2 — the route catalog states the truth

The operator named glm 5.3; the route template pins glm-5.2; the model
catalog warned glm-5.2 is not described. The routes should say what
they serve.

## Ground truth (measured 2026-09-20)
- the template: .rumpun/rumpun.yaml routes glm - `claude -p --model
  glm-5.2`; the catalog warning at the four-review dispatch said
  glm-5.2 is not in this version's model catalog
- the detection: `rumpun models --write` wrote 9 routes (glm, claude,
  gpt-6-astra, and others) at the s121 live init spot-check
- the hazard: rumpun.yaml is the campaign config - a broken route
  breaks future launches, so the new template is proven with ONE
  bounded probe call before landing, never guessed
- the surfaces that must agree: the route template, the models
  detection output, docs/campaign-guide.md's route claims

## Task
1. Probe glm-5.3 once (bounded, one call); if it serves, update the
   glm route template to it; if not, keep 5.2 and record the probe
   output in notes.md - either outcome lands, the probe decides. Re-run
   models --write and align docs/campaign-guide.md's route claims.
   Pins red-first in tests/test_s125_route_catalog.py (the route
   template and the guide's claims agree on the version string).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: .rumpun/rumpun.yaml (the glm route line), docs/campaign-guide.md
  (the route claims), tests/test_s125_route_catalog.py only. notes.md
  REQUIRED.
