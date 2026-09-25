# s136 w1 — the full guide re-linted, the readme re-proven

The s121 pin lints the guide's close path; the s128 pin guards the
readme table. The rest of the guide's sections can still drift.

## Ground truth (measured 2026-09-21)
- the pins: tests/test_s121_campaign_guide.py (the close path),
  tests/test_s128_readme_verbs_lint.py (the readme table)
- the guide: docs/campaign-guide.md sections 1, 2, and 4 carry
  commands beyond the close path (init, models, graph, lint, season
  verbs, audit, evolve)
- fixture discipline: read-only pins; no writes anywhere

## Task
1. Extend the lint: every command in every guide section parses
   against the current parser; the readme verbs table re-proven.
   Pins red-first in tests/test_s136_full_guide_lint.py.
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s136_full_guide_lint.py, docs/campaign-guide.md
  and README.md ONLY for named drift. notes.md REQUIRED.
