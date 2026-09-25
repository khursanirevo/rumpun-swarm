# s61 w1 — the pipeline tells the truth

You are w1 in season s61 (repo root: the parent of this .rumpun tree).
Read src/rumpun/lint.py, src/rumpun/audit.py (the F1 phase-liveness
finding and audit-41's candidate), src/rumpun/engine.py (what the
pipeline block actually drives), and ledger records s60-harvest +
audit-41. FILE TOOLS directly. WRITE ONLY inside your workspace EXCEPT
minimal documented code changes. 40 minutes.

## The candidate (audit-41, first in pipeline order)

results.jsonl written in 0 of 10 engine seasons (s51-s60) while every
season yaml declares execute->evaluate. Two routes, pick by evidence and
record the choice in notes.md:
- EXERCISE: the pipeline path writes results.jsonl for real (the
  declared phases produce their declared artifacts).
- TRIM: the schema stops requiring the pipeline block; the F1 finding
  retires with it.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- Additive or cleanly-trimming: the suite floor holds; the known race
  flakes stay the only reds.
- The falsify gate (a reachable reader for every declared write) and the
  stall record stay intact whichever route you take.

## Verify before finishing
If EXERCISE: a stub season run leaves results.jsonl in its ledger dir.
If TRIM: a pipeline-less yaml lints, starts, and the F1 finding no
longer counts it. Suite floor. All in notes.md.
