# s143 w2 — the fixed pipeline proves real lane work

w1 lands the per-lane briefs; this lane proves the fixed template's
pipeline end to end in a tmp campaign: a template-seeded season whose
lanes produce real artifacts.

## Ground truth (measured 2026-09-21)
- the s142 LOSS: the template-seeded season's lanes ran the generic
  prompt and produced nothing (no artifacts, no notes, three gate
  marks)
- the tmp-campaign convention: init in tmp; the season runs with the
  stub or light config; the real campaign never touched
- the honest proof: the lanes produce their named artifacts (the
  sweep, the probes, the rehearsals records) and notes.md - or the
  test names what is still missing

## Task
1. Script the fixed pipeline's walk in a tmp campaign: init, seed the
   steady-state season from the template, run it light, and capture
   the artifacts and the notes. Pins in
   tests/test_s143_pipeline_proof.py (the walk as a test; the
   artifacts exist and carry lane work; the notes exist).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s143_pipeline_proof.py,
  .rumpun/seasons/_steady-state.yaml (only if the walk exposes a
  template drift) only. notes.md REQUIRED.
