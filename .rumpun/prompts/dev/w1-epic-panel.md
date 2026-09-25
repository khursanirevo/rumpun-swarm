# s111 w1 — the epic member render names its second opinion

The s110 render names each member's basis; the panel verdict records
already exist (six sealed 09-17, five more sealing at this close). The
next honesty step: the member line names its latest panel verdict.

## Ground truth (measured 2026-09-20)
- the render: src/rumpun/epics.py (the s110 member-line extension; the
  s110 DESIGN entry is the ground truth)
- the verdict records: panel-<sid>-verdict in .rumpun/ledger/ -
  panel-s70-verdict (WIN), panel-s74-verdict (LOSS), panel-s75-verdict
  (WIN), panel-s76-verdict (WIN), panel-s77-verdict (LOSS),
  panel-s78-verdict (WIN); more seal at the s110 close sweep
- akar.declared_ids resolves records; -2/-3 suffixes are the s108
  rerun convention; the highest generation wins
- bounds precedent: the s110 w1 disclosure (tests/test_s89_w2_pins.py
  line 252 moved with the render shape) - probe the pin surface before
  assuming the member-line shape is unpinned

## Task
1. Extend the member render: a member whose family has a latest
   panel-<sid>-verdict record names it (a compact panel mark consistent
   with the basis format); members without one stay honest (no
   invented verdicts). Epic rows and the rollup sums unchanged. Pins
   red-first in tests/test_s111_epic_panel.py (the s108 fixture
   pattern: real yamls, real sealed records, no network).
2. Verify over the real campaign: s70 and s74-s78 members name their
   verdicts; full suite green vs the known reds (solo-run any new red
   before calling it a regression); ruff clean.
3. notes.md REQUIRED before ending the turn: the render lines, the
   pins result, the suite count. Never wait on a background job at
   turn end (the s108 w1 lesson).

## Bounds
- Edits: src/rumpun/epics.py, src/rumpun/cli.py (the epics verb
  only), tests/test_s111_epic_panel.py only. notes.md REQUIRED.
