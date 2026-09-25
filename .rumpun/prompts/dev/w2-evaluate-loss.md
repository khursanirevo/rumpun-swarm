# s135 w2 — evaluate emits the LOSS it meets

Issue #47: F3 reads WIN 10 / LOSS 0 across s77-s86 while s85 met a
LOSS condition. The judge reads WIN-only; the record lies by omission.

## Ground truth (measured 2026-09-20)
- the evaluate path: the judge prompt (prompts/base/evaluate.md) and
  its emitting code (src/rumpun/evaluate or the engine's judge phase)
- the history: the s77-s86 verdict rows read WIN 10 / LOSS 0 while
  s85's own band text carried a met LOSS condition
- the honest shape: a met LOSS condition reads LOSS, verbatim in the
  verdict row; a WIN that met its band still reads WIN (no inversion)
- fixture discipline: tmp fixtures; the real verdict rows never
  rewritten

## Task
1. Fix the path: the evaluate logic (and the prompt text if it shapes
   the behavior) emits a met LOSS condition as LOSS. Pins red-first in
   tests/test_s135_evaluate_loss.py over the s85 fixture shape (the
   band text and the observed result the issue names).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: the evaluate module, prompts/base/evaluate.md (if the prompt
  shapes the behavior), tests/test_s135_evaluate_loss.py only.
  notes.md REQUIRED.
