# s14 w1 — engine spawn tool-check (detect tool-less boots at spawn time)

You are w1 in season s14 of the rumpun campaign (repo root: the parent of
this .rumpun tree). Read DESIGN.md sections 13 and 15 first, then
src/rumpun/engine.py (the spawn + watcher + finalize path) and the akar
records glm-toolless-spawn and audit-2 (.rumpun/akar/2026-09-14_*.md).

## Problem (evidence-cited)

Some spawned agents boot WITHOUT working file/exec tools: they stream a
plan into agent.log, write nothing, exit 0. 7 of 24 glm spawns through s12
(akar:glm-toolless-spawn); audit-2 counts 6 clean-empty of 19 glm spawns in
its window. Today this is only visible post-hoc at season close. Your job:
give the engine a spawn-time detector that marks such snaps in state.json.

## Deliverables (write ONLY inside your workspace; the harness merges)

1. notes.md — the signature analysis and your patch as targeted diffs.
2. The engine patch spec if you have file tools; if you do not, author the
   full patch in agent.log AND notes.md (salvage pattern, s4/s6/s7
   precedent) and say so in notes.md.

## Signature analysis (do this first, empirically)

Compare real logs on disk:
- known tool-less: .rumpun/rimba/s4/w1, s5/w2, s6/w1, s6/w3, s7/w1, s8/w2,
  s12/w1 (agent.log in each)
- known clean: .rumpun/rimba/s13/w1, s13/w2, s11/w1, s11/w2
Find a discriminator that is deterministic (no timestamps, no pids, no
paths that vary). If NO deterministic discriminator exists, stop, say so in
notes.md with the counterexamples, and propose the nearest observable.
Never log or return token VALUES; log file paths and byte offsets only.

## Detector contract (pin this shape)

- Function: pure classifier `log_signature_toolless(text: str) -> bool`
  importable from rumpun.engine (w2 pins it spec-first).
- The existing watcher cycle calls it on each live agent's agent.log once
  the log has non-trivial content and the agent has produced no exit file;
  on the FIRST positive it sets snap["toolless"] = true, logs a WARNING
  (logger, not print), and appends one lane event on the collab lane
  (existing _child_env lane wiring). One check per watcher cycle — no new
  sleep loops, no polling beyond the watcher's existing cadence.
- Additive key only: never rewrite existing snap keys; report.py and the
  audit must keep working unchanged (the suite will prove it).
- Re-check semantics: once marked, never unmarked; a later exit file still
  classifies the snap by the existing rules.

## Constraints

- logging, never print; ruff check clean (line-length 100); py3.10+.
- One mechanism: if a second idea looks tempting, write it in notes.md as
  a future candidate instead.
- Do not touch cli.py, audit.py, report.py, or tests/ — w2 owns the test
  contract; the harness merges.
- Never include API keys or token values in anything you write.

## Verification before you finish

Run the repo suite against your patched engine in a scratch copy (uv run
pytest) and state the result in notes.md. Replay your classifier over ALL
real logs s3-s13 (.rumpun/rimba/s*/w*/agent.log) and put the confusion
matrix in notes.md: tool-less corpus must classify true, clean corpus
false, any miss listed explicitly.
