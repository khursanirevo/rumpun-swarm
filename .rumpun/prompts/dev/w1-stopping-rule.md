# s94 w1 — the stopping rule and the aggregate question (the composer's governance candidates)

Two governance residuals, distilled by the composer: s30/s32 count
post-stop integration as WIN while earlier salvaged seasons retain
LOSS (aggregate inconsistency), and automatic continuation lacks a
demonstrated stopping rule once actionable candidates disappear.

## Ground truth (measured 2026-09-18)
- audit-46's candidates (the fresh composer run, w1 s93 notes): the
  two governance lines; #16's sibling slices landed in s93
- the campaign's verdict history: salvaged seasons (s59, s66, s67,
  s90's live-test shape) and the aggregate slot table (the s64
  composer counts the whole ledger)
- the assessment standing step (s88): CONTINUE/PAUSE/EXHAUSTED is
  answered per close — the stopping-rule residual asks what THRESHOLD
  flips CONTINUE to EXHAUSTED

## Task
1. The aggregate question: measure it — the slot table's WIN count
   includes post-stop-integration verdicts (seasons that landed WIN
   after their lane stopped). Reconcile honestly: either the slots
   separate `WIN (in-lane)` from `WIN (post-stop integration)` with
   the count unchanged, or document why the aggregate is honest as-is.
   Land the chosen reconciliation as a composer test
   (tests/test_s94_w1_pins.py, _s94w1_ prefix, offline).
2. The stopping rule: design the threshold — what concrete, checkable
   state flips the assessment to EXHAUSTED (e.g., N consecutive
   assessments with zero actionable candidates AND no operator-gated
   fronts moved). Distill into the kancil-base pack as
   priors/templates/stopping-rule.md. Pin the template's parse.
3. notes.md REQUIRED: the reconciliation, the threshold, the pin map.

## Bounds
- Edits: tools/usefulness_audit.py (the slot label only, if chosen),
  the pack draft (one template), tests/. notes.md REQUIRED. No audit
  run (w2's lane owns the next one... no audit lane this season; the
  pins carry it).
