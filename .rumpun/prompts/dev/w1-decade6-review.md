# s116 w1 — the decade-6 different-model review finally runs

The eighth assessment named it: the decade-6 different-model review has
waited behind the credit gate twice; the credits are live since the
09-20 panel sweep. Run it and seal it.

## Ground truth (measured 2026-09-20)
- the front: named in the s106 evidence trail and the usefulness-s114
  fronts - the review of the early-season decade by a different model,
  unrun since the credits gate
- the route seam: src/rumpun/panel.py gpt6_astra_route (the same
  gpt-6-astra subprocess route the panel sweep used on 2026-09-20,
  four real verdicts sealed); the audit verb surfaces sit in
  src/rumpun/audit.py
- the ledger: the early-season records are committed history; the
  review reads them, it never rewrites them
- the cost rule: the operator restored the credits for exactly this
  class of run; one bounded review call (the panel route's 300s bound
  is the precedent), never a loop

## Task
1. Scope the decade from the ledger (enumerate the early-season
   records first; the brief lags), compose the review request, run it
   once through the route, and seal the reply as a named audit record.
   If the route refuses, seal the error record naming the concrete
   blocker - both outcomes are honest closes.
2. Verify: the record sealed and readable back; full suite green vs
   the known reds (solo-run any new red); ruff clean if any src file
   moved.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: the sealed record (ledger), src/rumpun/audit.py ONLY if the
  surface needs a seam, and no other src files. notes.md REQUIRED.
