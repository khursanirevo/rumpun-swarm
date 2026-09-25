# s95 w2 — the season grammar accepts "fix" (the recorded annoyance, made structural)

The RESUME conventions record it: "the season grammar's change types
exclude 'fix' — a filed-defect repair maps to 'retune'". Three closes
stumbled on it (s79, s91, and the s93-adjacent shape). Fix the
grammar: "fix" joins the change-type enum as a first-class repair
type, and the record-keeping maps filed-defect repairs to it instead
of the retune euphemism.

## Ground truth (measured 2026-09-18)
- the enum: evolve apply refuses anything outside [add, emergency,
  free_bundle, pipeline_switch, remove, retune, rewire,
  rollback_restore] (hit live at s79 and s91)
- the season yamls that WANTED fix: s79, s91 (both typed retune under
  protest), s93's composer candidates named it
- the grammar: src/rumpun/evolve.py (the apply-side validation) +
  wherever the enum is defined

## Task
1. Fix the enum: "fix" joins the change types (the validation, the
   docs string, wherever the list lives). The existing types stay
   valid; nothing breaks.
2. Pins (tests/test_s95_w2_pins.py, _s95w2_ prefix, offline): "fix"
   applies clean (a fixture yaml typed fix), the old eight types
   still apply (no regression), an unknown type still refuses.
3. The record-keeping: the RESUME conventions line updates (the
   mapping sentence retires) and the CHANGELOG gains the Added line.
4. notes.md REQUIRED: the diff, the pin list.

## Bounds
- Edits: src/rumpun/evolve.py, .rumpun/RESUME.md (one line),
  CHANGELOG.md (your Added line lands in the s95 close's section),
  tests/. notes.md REQUIRED.
