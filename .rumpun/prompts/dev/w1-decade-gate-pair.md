# s134 w1 — the decade gate stops nagging on edge cases (issues #45 and #51)

Two filed defects on the same conventions: the audit F7 gate and the
drought hint both mishandle the usefulness-decade records' scope.

## Ground truth (measured 2026-09-20)
- issue #45: the audit F7 usefulness-decade gate ignores record scope -
  a permanent false nag at high season velocity.
- issue #51: the evolve plan assessment-due warning never silences when
  only decade records exist (the s122 date rule covers the s-series
  stopper, but a decade-only ledger keeps the hint firing).
- the rule seams: src/rumpun/evolve.py _assessment_due (the s116/s122
  hint) and the audit F7 gate (src/rumpun/audit.py, the decade gate)
- the conventions: the per-close seals (usefulness-s<N>), the decade
  reviews (usefulness-decade-<N>), and the s122 date-window rule are
  the semantics both fixes must reconcile, not override
- fixture discipline: tmp campaigns; records via akar.append_record;
  the real ledger never written in tests

## Task
1. Fix both: the F7 gate scopes the decade records it reads (a
   relevant-scope decade review satisfies the gate; an out-of-scope one
   does not falsely nag), and the drought hint silences when a
   decade-only ledger's coverage is current (per the s122 date rule,
   generalized to the no-s-series case). Pins red-first in
   tests/test_s134_decade_gate_pair.py (tmp campaigns).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/evolve.py, src/rumpun/audit.py,
  tests/test_s134_decade_gate_pair.py only. notes.md REQUIRED.
