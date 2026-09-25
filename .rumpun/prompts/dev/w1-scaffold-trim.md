# Task: trim the init scaffold pipeline to execute -> evaluate (full scaffold.py into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s12/w1. Write ONLY scaffold.py,
notes.md, lane_tool.py into this workspace. Do not touch anything outside it.

Base your scaffold.py on the CURRENT repo file
/mnt/data/work/rumpun/src/rumpun/scaffold.py (read it first; keep every
behavior and all 41 tests passing; do not edit tests/).

Evidence (akar audit-1): analyze, rank_gaps, hypothesize produced their
artifacts in 0 of 8 engine seasons; plan and falsify are also unexercised,
and the DAG forces their removal once the head goes (plan reads
hypotheses.yaml, falsify reads experiments.yaml). The lint-clean trim is a
2-phase pipeline: execute -> evaluate.

Changes, nothing else:
1. In the MUSIM_S1 constant: replace the 7-phase methodology.pipeline with
   exactly two nodes:
     - phase: execute, primitive: execute, agents: benih,
       prompt: prompts/base/execute.md, writes: results.jsonl
     - phase: evaluate, primitive: evaluate, agent: judge,
       prompt: prompts/base/evaluate.md, reads: results.jsonl,
       writes: verdicts.jsonl
2. Apply the same trim inside MUSIM_TEMPLATE (the non-seed shape keeps its
   primary_change block and everything else).
3. Do not touch prompts/base/*.md contents, the akar/rimba wiring, or any
   other constant.

Collab lane (protocol v2, NON-BLOCKING): post kind=start, kind=policy (the
exact 2-node pipeline you wrote), kind=done via lane_tool.py from
RUMPUN_LANE_FILE/RUMPUN_LANE_LOCK. Never wait on w2.

Rules: ruff clean, line-length 100, py3.10+. notes.md: what changed and what
you verified about lint compatibility (falsify-must-reach-execute only fires
when a falsify node exists).
