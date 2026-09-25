# s71 w2 — the panel's second-opinion route (issue #1, second slice)

s70 landed the panel's input contract (claim_set, render_review) and
the pending-record seal. This season wires the real route behind it.

## Ground truth
- src/rumpun/panel.py: claim_set, render_review (bounded one screen),
  request_review (--dry-run writes nothing; the real run appends a
  sha-sealed panel-<sid> record marked pending)
- cli.py: `rumpun audit --panel <sid> [--dry-run]` wired
- the decadal precedent: tools/usefulness_audit.py spawns gpt-6-astra
  bounded at 300s - the route pattern to copy

## Task (spec-first, pins in tests/test_s71_w2_pins.py, _s71w2_ prefix)
1. panel.py grows the route call: request_review without --dry-run
   sends render_review's text to the gpt-6-astra route (subprocess,
   bounded 300s), reads the reply, and the panel-<sid> record upgrades
   from pending to the verdict with the reply quoted (sha-sealed,
   append-only: the pending record stays, a new record carries it).
2. Route unreachable/timeout: the record seals as pending with the
   error quoted (never silent, never fabricated). No retries.
3. Pins: the route seam is a pluggable callable - pinned with a fake
   reply offline (argv construction, bounded timeout, record shapes
   for the healthy/timeout paths). No real route call in pins.
4. Live smoke (once, real): `rumpun audit --panel s69 --dry-run` renders;
   then one real `rumpun audit --panel s70` - record the outcome.

## Bounds
- 40-60 min budget. Edits: src/rumpun/panel.py, tests/ only. notes.md
  REQUIRED. No board.py, no kanban.py, no .rumpun state edits.
