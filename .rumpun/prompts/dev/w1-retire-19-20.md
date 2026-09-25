# s103 w1 — retire issues #19 and #20 on the landed evidence

The operator's two filed defects are fixed on current main (s102).
Your lane: the retirement comments carrying the sealed evidence, the
closes, and the operator-facing summary.

## Ground truth (measured 2026-09-18)
- issue #19: the engine staffs no pipeline phase by design; the real
  defect was the SCAFFOLD emitting the misleading singular agent:
  shape - fixed (the scaffold emits the spawnable plural), the engine
  contract pinned, the scaffold pin red-first on the emitted keys
- issue #20: reproduced on main @ eb761b0 (init emits 15 files,
  tools/ absent, the harvest close exit-2) - fixed (the scaffold
  ships tools/artifact_check.py via the _checker_source walk-up)
- the sealed evidence: ledger:s102-harvest (check-s102 VERIFIED at
  the close commit)

## Task
1. Retire #19: comment it with the evidence (the engine-staffs-nothing
   design truth, the scaffold fix, the red-first pin) citing the
   sealed s102-harvest record, then close it as completed.
2. Retire #20: the same shape (the literal repro on main @ eb761b0,
   the _checker_source walk-up fix, the pins) citing the sealed
   record, then close it.
3. The operator-facing summary: the two closes name the shipped tag
   (v0.11.0) as the repro surface and current main as the fix surface.
4. notes.md REQUIRED: the comment urls, the close confirmations.

## Bounds
- Two live comment+close pairs. Read-only otherwise. notes.md
  REQUIRED.
