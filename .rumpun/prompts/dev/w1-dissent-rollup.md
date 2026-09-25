# s117 w1 — the rollup renders the dissent adjustment

The decade-6 review named it: the assessment kept WIN totals despite
s79's NEUTRAL and s83's INCONCLUSIVE second opinions. The counts are
honest; the adjusted view is missing.

## Ground truth (measured 2026-09-20)
- the rollup: src/rumpun/epics.py (season_verdict at line 124, the
  s110 basis mark, the s111 panel mark, the s112 dissent mark; the
  rollup counts WIN/LOSS/other from the harvest rows)
- the review's residual, verbatim: "usefulness-s114 preserves WIN
  totals despite s79's NEUTRAL and s83's INCONCLUSIVE second opinions"
- the real members: s79 judge WIN with dissent:NEUTRAL, s83 judge WIN
  with dissent:INCONCLUSIVE, s69 judge other with dissent:LOSS
- bounds precedent: the s89/s111 shape pins moved twice with the
  render - probe tests/test_s89_w2_pins.py and
  tests/test_s111_epic_panel.py before assuming the rollup shape is
  unpinned

## Task
1. Extend the render: a member whose judge verdict is WIN and whose
   latest dissent is INCONCLUSIVE or NEUTRAL renders the adjustment
   beside the count (define the exact format, pin it); the raw counts
   stay verbatim, the adjusted view coexists, nothing is rewritten.
   Members without dissents stay as they are. Pins red-first in
   tests/test_s117_dissent_rollup.py.
2. Verify over the real campaign: s79 and s83 carry the adjustment;
   full suite green vs the known reds (solo-run any new red); ruff
   clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/epics.py, src/rumpun/cli.py (the epics verb only),
  tests/test_s117_dissent_rollup.py only. notes.md REQUIRED.
