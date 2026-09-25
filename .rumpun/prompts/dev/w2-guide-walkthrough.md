# s130 w2 — the guide's happy path proven end to end

The guide walks a fresh repo from zero to a sealed season; the walk
has never been scripted and pinned. Prove it.

## Ground truth (measured 2026-09-20)
- the guide: docs/campaign-guide.md (init, the fills, graph, lint,
  season start, status, harvest, check, the loop)
- the tmp-campaign convention: init in tmp; the real campaign never
  touched; the s121 live spot-check is the precedent (init and routes
  verified, no season run)
- the cheapest honest season: a minimal yaml with the smallest budget
  and the config the scaffold allows - the walk proves the PATH, not
  the writer quality
- fixture discipline: everything in tmp; no real ledger writes

## Task
1. Script the walk: a tmp campaign runs the guide's steps end to end -
   init, fill, graph, lint, a minimal season start to completed,
   harvest, check - every step's rc captured. Pins in
   tests/test_s130_guide_walkthrough.py (the walk as a test; tmp
   only). Doc drift found on the way lands in notes.md and, if real,
   a guide fix within bounds.
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s130_guide_walkthrough.py, docs/campaign-guide.md
  (only drift the walk exposes) only. notes.md REQUIRED.
