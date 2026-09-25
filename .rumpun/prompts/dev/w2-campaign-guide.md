# s121 w2 — the campaign guide for the next repo

The campaign's oldest operator ask: how do I run this on my own
project? The verbs are documented; the path from zero to a sealed
first season is not.

## Ground truth (measured 2026-09-20)
- the entry verbs: rumpun init (the scaffold), rumpun evolve plan /
  apply, rumpun season start / status / list, rumpun harvest, rumpun
  check, rumpun loop - the README's verbs table is current
- the campaign's own history is the worked example: seed from
  DESIGN.md, draft from the parent, fill the yaml, apply, start,
  harvest at close, check at HEAD, push - the close protocol in
  .rumpun/RESUME.md is the operator-facing loop
- the gates a fresh repo hits: the design lint (surfaces must exist),
  the pack digest (absent until a plugin exists), the schema (version
  1), the notes gate (writers owe notes.md)
- fixture discipline: docs only; no src changes; no real campaign
  writes

## Task
1. Write docs/campaign-guide.md: point rumpun at a fresh repo (init,
   the first season yaml, the first seed), run the first season
   (start, the writers, the gate), close it (harvest, the check, the
   push), and keep going (the loop, the planner's assessment warning,
   the board sync). Every command verified against this campaign's
   real surfaces - name the verbs exactly as the parser accepts them.
   The readme links the guide.
2. Verify: full suite green vs the known reds (solo-run any new red);
   ruff clean; the guide's commands spot-checked live (init in a tmp
   campaign at minimum).
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: docs/campaign-guide.md (new), README.md (the link only),
  tests/test_s121_campaign_guide.py (optional command-lint) only.
  notes.md REQUIRED.
