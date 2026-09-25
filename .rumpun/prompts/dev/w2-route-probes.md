# s136 w2 — every writer route probe-checked

The routes block names nine routes; only glm-5.3 and the panel route
have been probe-checked. The operator decides on the external
workload; the routes should be known-serving first.

## Ground truth (measured 2026-09-21)
- the routes block: .rumpun/rumpun.yaml routes (glm-5.3, fable,
  gpt-6-astra, gpt-reserve, gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna,
  gpt-5.5, codex-auto-review)
- the probe precedent: the s125 glm-5.3 probe (one bounded call; the
  catalog warning is CLI-side text, not a serving error)
- the honest record: a route that serves is recorded serving; a route
  that fails is recorded failing with the error - both are the truth
- fixture discipline: one bounded call per route; never a loop of
  retries; the fable route is this campaign's own writer route and
  needs no probe (it is running the season)

## Task
1. Probe each probeable route once (bounded call, exact template
   shape), record the serve table in notes.md (route -> serving or
   the named error). A probe-record shape pin in
   tests/test_s136_route_probes.py (the table exists and names every
   probeable route; reads only).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s136_route_probes.py, the probe record (notes.md)
  only; .rumpun/rumpun.yaml ONLY if a route proves broken and the fix
  is its own template correction. notes.md REQUIRED.
