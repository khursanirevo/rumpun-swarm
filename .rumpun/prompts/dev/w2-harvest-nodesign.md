# s115 w2 — the close check names the missing convention (issues #36 and #37)

Two filed defects on the same seam. A campaign repo whose extract
carries no design-convention file makes the harvest close check refuse
exit 2 - indistinguishable from a tamper refusal.

## Ground truth (measured 2026-09-20)
- issues #36 and #37: the harvest close check structurally refuses
  (exit 2) when the campaign repo has no DESIGN.md convention; the
  refusal is indistinguishable from tamper.
- the checker: tools/artifact_check.py - the ships-row and surface
  passes read the design convention file from the extract; the harvest
  verb's ride-along check calls it (src/rumpun/harvest.py).
- the locator caution: the pin locators key on committed campaign
  files (pyproject + src/rumpun/report.py + the design file) - do NOT
  weaken that convention; fresh-init campaign repos without the design
  file are the case to name, not to crash on.
- the s63 precedent: a false positive became a named skip (exit 0 with
  a line). The named skip is the house style.

## Task
1. Fix both: an extract whose tree carries no design-convention file
   produces a named skip line (a distinct verdict line naming the
   missing convention) instead of a bare exit 2 refusal; repos WITH
   the convention are byte-unchanged. Pins red-first in
   tests/test_s115_harvest_nodesign.py (build the no-design fixture
   tree in tmp; never copy .rumpun/runs/).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tools/artifact_check.py, tests/test_s115_harvest_nodesign.py,
  and src/rumpun/harvest.py (only the ride-along plumbing) only.
  notes.md REQUIRED.
