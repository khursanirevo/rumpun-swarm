# Task: write src/rumpun/audit.py + wire `rumpun audit` (audit.py and cli.py into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s11/w1. Write ONLY audit.py,
cli.py, notes.md, lane_tool.py into this workspace. Do not touch anything
outside it.

Base cli.py on the CURRENT repo file /mnt/data/work/rumpun/src/rumpun/cli.py
(read it first; keep every behavior and all 31 tests passing; do not edit
tests/). audit.py is a new module.

Purpose (DESIGN section 15): self-evolution needs reflection — the verb reads
the season ledger and produces evidence-cited candidate mutations. It never
mutates anything except appending its akar record.

API to write (module rumpun.audit):

  def run_audit(root: Path, last_n: int = 10) -> Path
  - seasons = musim/s*.yaml sorted by number, take the last `last_n`.
  - For each season sid with a rimba/<sid>/ dir, collect which ledger
    artifacts exist: errors.jsonl, gaps.yaml, hypotheses.yaml,
    experiments.yaml, falsification.yaml, results.jsonl, verdicts.jsonl,
    report.html.
  - Declared phases: read the LATEST season yaml, its methodology.pipeline:
    list of (phase, writes) pairs. Phase liveness = for each declared phase,
    in how many of those seasons its `writes` artifact exists on disk.
  - Findings computed from that data (deterministic rules, all cited by
    season ids):
    F1 phase liveness: "phase P wrote its artifact in K of N engine seasons"
    F2 stall recurrence: count seasons whose state.json status is
       stopped_stall; note count >= 2 as a recurrence finding
    F3 verdict histogram: WIN/LOSS/INVALID counts from verdicts.jsonl files
  - Candidates: at most 3 mutation proposals, each one line with its citing
    seasons and an expected band. Deterministic triggers:
    a phase with liveness 0 in >= 2 seasons -> "exercise or trim phase P"
    stopped_stall count >= 2 -> "re-size stall/budget rules"
    (never more than 3; never invent evidence)
  - Append an akar record: id f"audit-{next_index}" (next_index = 1 + count
    of existing audit-* ids in akar/, computed by scanning akar/ filenames),
    title "reflection audit", body = the findings + candidates, each line
    citing season ids. akar.AkarError wraps into AuditError.
  - Return the record path.

class AuditError(Exception)

cli.py:
- New TOP-LEVEL verb: rumpun audit [--last N]
  calls run_audit(root, last_n), prints the record path and the candidate
  lines (the verb's own output may print). Docstring version note v0.10.0,
  Implemented line gains audit.

Collab lane (protocol v2, NON-BLOCKING): post kind=start, kind=policy
(your exact candidate triggers), kind=done via lane_tool.py from
RUMPUN_LANE_FILE/RUMPUN_LANE_LOCK. Never wait on w2.

Rules: stdlib only; ruff clean, line-length 100, py3.10+. notes.md: the
trigger rules you implemented and any you deliberately left out.
