# s117 w2 — the replay matrix classifies its skips

The decade-6 review named it: the replay matrix runs five scripts and
skips 140, including unclassified replacements. The matrix should say
which is which.

## Ground truth (measured 2026-09-20)
- the matrix: replay-matrix.md (tracked, churns per suite run; the
  repro-out-clobber precedent: version capture paths per run)
- the corpus verb: tools/replay_corpus.py (the s30 refresh; the audit
  --corpus rides it)
- the review's residual, verbatim: "replay-matrix.md runs five scripts
  and skips 140, including unclassified replacements. Historical replay
  coverage remains incomplete."
- the churn lesson: captures overwrite their .out files; version the
  paths before the first run

## Task
1. Classify the matrix: every script the corpus knows carries a class
   - run, skip (with the named reason), or replacement-of (naming the
   script that covers it) - nothing unclassified. The classification
   lives with the matrix; a pin or lint asserts it over the real
   matrix. Pins red-first in tests/test_s117_replay_classify.py.
2. Verify: the classification over the real matrix is complete (no
   unclassified rows); full suite green vs the known reds (solo-run
   any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tools/replay_corpus.py, replay-matrix.md,
  tests/test_s117_replay_classify.py only. notes.md REQUIRED.
