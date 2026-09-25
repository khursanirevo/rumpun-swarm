# s110 w1 — the epic view names each member's basis

The integration pass: the s108 fold landed with the s106 no-record
basis named in the yaml; the rendered view should carry that honesty
to the reader, not keep it in the file.

## Ground truth (measured 2026-09-20)
- the verb: rumpun epics (cmd_epics, src/rumpun/cli.py:592); the
  renderer lives in src/rumpun/epics.py
- .rumpun/epics.yaml: board-arc holds s69-s107; the s108 fold added
  the basis: block - the rollup reads the last verdict row per member
  from run state plus run-state presence; s106 rides as other (the
  no-record basis named); s107 carries WIN from s107-harvest@fed94036
- the current render prints the X WIN / Y LOSS / Z other rollup and
  marks run-state-less members; the basis lives only in the yaml
- the s108 rerun convention (src/rumpun/panel.py) kept
  latest_panel_record generation-aware; the ledger never rewrites

## Task
1. Extend the epics render: each member line names its basis - a WIN
   member names its record id@sha-prefix, an other member names the
   basis string it declared. The yaml lint stays green; the rollup
   sum is preserved. Pins red-first in tests/test_s110_epic_basis.py
   (the s108 fixture pattern: real yaml, real records, no network).
2. Verify: the render over the real campaign names s106's basis and
   s107's record; full suite green vs the known reds (solo-run any
   new red before calling it a regression); ruff clean.
3. notes.md REQUIRED before ending the turn: the render lines, the
   pins result, the suite count. Never wait on a background job at
   turn end (the s108 w1 lesson).

## Bounds
- Edits: src/rumpun/epics.py, src/rumpun/cli.py (the epics verb
  only), tests/test_s110_epic_basis.py only. notes.md REQUIRED.
