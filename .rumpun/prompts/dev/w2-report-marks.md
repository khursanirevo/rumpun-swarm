# s113 w2 — the machine report renders the marks

The epic view carries the basis, the panel mark, and the dissent mark;
the deterministic report still shows bare exits. The machine view
catches up.

## Ground truth (measured 2026-09-20)
- the report: src/rumpun/report.py renders from persisted state alone
  (read_persisted_status: identical state.json bytes produce identical
  pages, the M1 determinism contract)
- the s112 gate: an rc-0 writer exit without notes.md gains the
  additive incomplete key on the snap (src/rumpun/engine.py
  _agent_snap) and the results row (_write_results)
- the marks to render: the incomplete key on the agent list; the
  dissent mark needs the harvest verdict plus the panel record - reuse
  the epics.py resolution (season_verdict, the highest-generation
  panel-<sid>-verdict), do not duplicate it
- fixture discipline: synthesize state in tmp_path; never copy from
  .rumpun/runs/ (the check-s110 class)

## Task
1. Extend the report: an agent entry carrying the incomplete key renders
   the mark; a season row whose member data yields a dissent renders
   the dissent mark. Identical inputs produce identical bytes (the M1
   contract holds). Pins red-first in tests/test_s113_report_marks.py.
2. Verify: solo pins green; the live report over the campaign renders
   the s112-shaped marks where they exist; full suite green vs the
   known reds (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/report.py, tests/test_s113_report_marks.py only.
  notes.md REQUIRED.
