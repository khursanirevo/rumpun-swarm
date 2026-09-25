# s113 w1 — the audit names the second opinion

The render names the dissent; the audit review surface still lists
seasons bare. The review at a glance: the audit --last output gains the
panel column.

## Ground truth (measured 2026-09-20)
- the verb: rumpun audit --last N (src/rumpun/audit.py; dispatched from
  cmd_audit in src/rumpun/cli.py)
- the resolution to reuse, not duplicate: src/rumpun/epics.py -
  season_verdict (line 124), the s110 basis mark, the s111 panel mark
  (highest panel-<sid>-verdict generation wins), the s112 dissent rule
  (dissent only when both sides exist and differ)
- the known real-ledger rows: s69 judge other / panel LOSS, s79 judge
  WIN / panel NEUTRAL, s83 judge WIN / panel INCONCLUSIVE, s84 judge
  WIN / panel WIN (bare - agreement is not news)
- fixture discipline: the s108 pattern (real yamls, hand-sealed
  records); never copy from .rumpun/runs/ (the check-s110 class)

## Task
1. Extend the audit --last listing: each season row names its judge
   verdict, its latest panel verdict, and a dissent flag when the two
   exist and differ. Seasons without panel records stay bare. No
   invented verdicts. Pins red-first in
   tests/test_s113_audit_panel_col.py.
2. Verify over the real ledger: the rows for s69, s79, s83, s84 carry
   the right panel verdicts and flags; full suite green vs the known
   reds (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/audit.py, src/rumpun/cli.py (the audit verb only),
  tests/test_s113_audit_panel_col.py only. notes.md REQUIRED.
