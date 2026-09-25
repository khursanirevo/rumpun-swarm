# s36 w1 — stall-resume logic in evolve draft_next

You are w1 in season s36 (repo root: the parent of this .rumpun tree). Read
src/rumpun/evolve.py (draft_next + _latest_season), src/rumpun/engine.py
(read_persisted_status), and akar records audit-25 + s30-harvest + s32
evidence. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Deliverable: draft_next resumes a stopped_stall parent

Today: draft_next copies the parent season verbatim regardless of how it
ended. Three stall-killed seasons each needed a manual re-scope, re-cite,
and budget re-tune (s17->s18 manual, s30->s31 manual, s32->s33 manual).
Fix in draft_next: after loading the parent season yaml, read the parent's
persisted engine state (engine.read_persisted_status on the parent sid);
if its terminal status is stopped_stall:
- the drafted budget for every benih is the parent's times 1.5 (rounded
  up to whole minutes), recorded in the yaml header comment: "resumed
  from stopped_stall parent <sid>; budget 40 -> 60 min";
- the yaml header comment gains a stall citation line naming the parent's
  status.
Non-stall parents: behavior byte-identical to today.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch engine.py, lint.py, akar.py, cli.py, report.py, tests/
  (w2 owns the pins; the harness merges).
- The 171-test suite stays green.

## Verify before finishing

Repros: a stopped_stall parent (fixture state) drafts with 1.5x budgets
and the stall citation header; a completed parent drafts byte-identical
to today. Suite green against patched copies. Both in notes.md.
