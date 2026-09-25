# s102 w1 — issue #19: the singular-agent evaluate phase

The khursani campaign (v0.11.0) declared an evaluate phase with
singular `agent: judge`; the engine spawned nothing for it and the
verdicts artifact never appeared. Reproduce on CURRENT main first:
fixed since 0.11.0 → close with evidence; still broken → fix.

## Ground truth (measured 2026-09-18)
- issue #19 (OPEN): the issue's own yaml snippet is the spec —
  execute phase `agents: writers` spawned both; evaluate phase
  `agent: judge` spawned nothing; all_exited fired; verdicts.jsonl
  never appeared
- the CURRENT campaigns' evaluate phases also declare singular
  `agent: judge` — and audit-45's F1 measured verdicts.jsonl written
  in 9 of 9 seasons. The divergence is the first thing to explain.
- the repro: the issue's literal yaml shape on a fresh campaign

## Task
1. Reproduce on current main: a fresh campaign whose season yaml
   carries the issue's literal evaluate shape (singular `agent:`).
   Spawn; measure what the engine does (the judge spawned? the
   artifact written?).
2. Branch per the evidence: (a) the current engine handles the
   singular shape and 0.11.0 did not → close #19 with the fix-commit
   evidence; (b) the current engine also refuses the singular shape
   (the verdicts artifact comes from elsewhere) → fix the smallest
   surface (the engine supports `agent:` as a one-element list, or
   the scaffold emits the plural — per the code's shape) with pins
   (tests/test_s102_w1_pins.py, _s102w1_ prefix, offline).
3. notes.md REQUIRED: the reproduction, the branch taken, the
   evidence.

## Bounds
- Edits: src/rumpun/ (the engine or the scaffold, per the evidence),
  tests/. notes.md REQUIRED. The khursani campaign is read-only
  evidence (its files are the spec).
