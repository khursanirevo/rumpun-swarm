# s143 w1 — the template's phases get real briefs

The s142 LOSS named the defect: the steady-state template's phases
pointed at the generic execute prompt with no lane specification, so
the lanes produced nothing. The fix: per-lane briefs.

## Ground truth (measured 2026-09-21)
- the template: .rumpun/seasons/_steady-state.yaml (the phases:
  lint-sweep, route-probes, rehearsals, decision-gate; the artifacts:
  sweep/probes/rehearsals/gate-report .jsonl)
- the defect: the phases' prompt fields all pointed at
  prompts/base/execute.md, which carries no lane work
- the brief pattern: prompts/dev/w1-light-lanes-sweep.md and
  w2-rehearsals-reconfirm.md (the s139 lanes' real briefs - the
  content the template phases should carry)

## Task
1. Land the briefs: the scaffold emits three per-lane prompt files
   beside the template (the lint-sweep brief, the route-probes brief,
   the rehearsals brief - each naming its lane work, its artifact,
   and the notes contract, adapted from the s139 lanes' briefs); the
   template's phases point at them. The init emission pinned
   red-first in tests/test_s143_template_briefs.py (tmp campaigns).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/scaffold.py, tests/test_s143_template_briefs.py
  only. notes.md REQUIRED.
