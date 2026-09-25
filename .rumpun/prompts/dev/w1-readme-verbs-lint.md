# s128 w1 — the readme's verbs table gets the parser guard

The guide's commands are parser-linted by a pin; the readme's verbs
table can drift silently. Same guard, second surface.

## Ground truth (measured 2026-09-20)
- the table: README.md's verbs table (refreshed at s118; the surface
  every reader sees first)
- the precedent: tests/test_s121_campaign_guide.py lints every guide
  command against cli.build_parser() - verbs, subverbs, flags
- the parser: src/rumpun/cli.py build_parser(); verbs missing from the
  table (epics, check, waive, models) are candidates to add
- fixture discipline: read-only pins; no writes anywhere

## Task
1. Land the pin: every README verbs-table row's command lints against
   the parser with drift named; add the missing verbs' rows. Pins
   red-first in tests/test_s128_readme_verbs_lint.py.
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: README.md, tests/test_s128_readme_verbs_lint.py only.
  notes.md REQUIRED.
