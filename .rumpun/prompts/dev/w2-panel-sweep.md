# s110 w2 — the panel learns to sweep pending outcomes

The integration pass: the rerun convention sealed panel-s69 and
panel-s69-2 pending; the outcome half waits on the operator's
gpt-6-astra credits. The sweep makes the wait legible and the seal
explicit.

## Ground truth (measured 2026-09-20)
- the rerun convention (src/rumpun/panel.py, s108): a second audit
  --panel run derives panel-<sid>-N; the first record never rewrites;
  outcomes seal as <id>-verdict or <id>-error beside the request
- the pending families: panel-s69 and panel-s69-2 (2026-09-20), plus
  the panel-s70..s84 records sealed at the earlier closes - all
  pending, all awaiting route outcomes
- the credit gate: the operator's; route outcomes cannot seal until
  it lifts (the s106 evidence trail captured the same gate)
- precedent: refusals get named conventions and records (the
  basis-supersede record, the one-row guard, the s108 derivation)

## Task
1. Add the sweep: audit --panel-sweep lists the pending panel records
   (id, date, status) and refuses exit 2 without an explicit
   --outcome-file; with one, it seals each named outcome as
   <id>-verdict or <id>-error beside the pending request - never
   invented, never rewriting. Pins red-first in
   tests/test_s110_panel_sweep.py (the s108 fixture pattern).
2. Verify: the sweep over the real ledger lists the pending ids and
   refuses bare; full suite green vs the known reds (solo-run any new
   red before calling it a regression); ruff clean.
3. notes.md REQUIRED before ending the turn: the listing, the bare
   refusal line, the pins result. Never wait on a background job at
   turn end (the s108 w1 lesson).

## Bounds
- Edits: src/rumpun/panel.py, tests/test_s110_panel_sweep.py, and the
  audit verb's flag plumbing in src/rumpun/cli.py only. notes.md
  REQUIRED.
