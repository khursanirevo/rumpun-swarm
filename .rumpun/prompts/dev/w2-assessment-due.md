# s116 w2 — the planner announces the assessment due

The standing assessment rode on memory: the harness noticed at s114
only because the close worker read the ledger. The planner should say
it.

## Ground truth (measured 2026-09-20)
- the planner: src/rumpun/evolve.py plan drafts the next season yaml
  from the parent (the drafting output this close chain runs on)
- the cadence facts: usefulness records at s87, s97, s98, s99, s101,
  s104, s107, s114 - the gap s107 to s114 crossed seven closes before
  the eighth sealed
- the enumeration: akar.declared_ids resolves usefulness-* records;
  the season lineage is the parent chain in .rumpun/seasons/*.yaml
- precedent: the planner already prints lint findings at apply; a
  named INFO/WARNING hint at plan time is the house style

## Task
1. Land the rule: evolve plan inspects the lineage behind the parent
   season; if the recent closes carry no usefulness record within the
   campaign's cadence (name the constant, pin the boundary), the plan
   output announces the assessment due with the last sealed id. A
   current lineage stays silent. Pins red-first in
   tests/test_s116_assessment_due.py (fixture campaigns in tmp; the
   real ledger never written).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/evolve.py, tests/test_s116_assessment_due.py only.
  notes.md REQUIRED.
