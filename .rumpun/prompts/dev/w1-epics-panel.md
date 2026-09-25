# s108 w1 — the epic folds s106-s107; the panel learns to rerun

The maintenance pass: the board-arc epic catches up with the closes
that trailed it, and the audit panel gains the rerun convention it
has lacked since s79.

## Ground truth (measured 2026-09-20)
- .rumpun/epics.yaml: board-arc holds s69-s105 (the s107 w1 call:
  the self-extensions kept pace; s106 stayed undeclared pending its
  close)
- s106: WIN per DESIGN (the installed pack synced a22944c1, the epic
  extended s93-s95, issue #18 carries the landed evidence) - but the
  s106-harvest record is absent by design (the harvest was refused
  by the one-row guard; the evidence lives in the DESIGN entry, the
  lane notes, and the check record)
- s107: WIN, record s107-harvest (read the sha from the record file)
- the refusal: audit --panel refuses a second run under the same
  request id (the s79 finding); a rerun needs a convention first
- precedent: refusals get named conventions and records (the
  basis-supersede record, the one-row guard); the ledger never
  rewrites

## Task
1. Fold s107 into the board-arc epic (the record exists; the
   members-equals-harvests partition holds). Decide s106 honestly:
   fold it with the no-record basis named, or leave it undeclared
   with the disclosure. Never invent a verdict; state the basis the
   rollup uses.
2. Fix the panel rerun refusal in src/rumpun/audit.py: a second
   --panel run lands under a derived or explicit second id without
   rewriting or deleting the first record. Pins red-first in
   tests/test_s108_panel_rerun.py.
3. Verify: the epic view sums to the whole ledger with the basis
   named; the panel runs twice cleanly; full suite green vs the
   known reds (solo-run any new red before calling it a
   regression); ruff clean.
4. notes.md REQUIRED: the epic view, both panel runs, the basis.

## Bounds
- Edits: .rumpun/epics.yaml, src/rumpun/audit.py,
  tests/test_s108_panel_rerun.py only. notes.md REQUIRED.
