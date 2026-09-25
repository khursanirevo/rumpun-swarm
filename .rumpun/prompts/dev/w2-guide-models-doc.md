# s128 w2 — the guide documents the models re-detect

The s126 verb taught models --write to re-read filled campaigns; the
guide's models section predates it and says nothing about what a
filled campaign gets.

## Ground truth (measured 2026-09-20)
- the section: docs/campaign-guide.md lines ~41-51 (read-only without
  flags, --probe spends quota, the placeholder keys, the glm-5.3 serve
  claim)
- the s126 behavior: on a filled campaign models --write diffs the
  detected routes against the config and writes only named additions,
  never clobbering, idempotent (src/rumpun/cli.py cmd_models,
  src/rumpun/routes.py; pinned by tests/test_s126_models_redetect.py)
- the guide's lint guard: tests/test_s121_campaign_guide.py fails the
  suite when a command here drifts from the parser
- fixture discipline: docs only; no src changes

## Task
1. Document the re-detect in the guide's models section: what a filled
   campaign gets (the diff, the named additions, the never-clobber
   rule, the idempotence), matching the s126 verb exactly. Extend the
   command-lint pins if the section gains commands:
   tests/test_s128_guide_models_doc.py red-first.
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: docs/campaign-guide.md, tests/test_s128_guide_models_doc.py
  only. notes.md REQUIRED.
