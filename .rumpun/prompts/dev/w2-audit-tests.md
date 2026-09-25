# Task: spec-first tests for run_audit (full test file into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s11/w2. Write ONLY
test_rumpun.py, notes.md, lane_tool.py into this workspace. Do not touch
anything outside it.

Base your test_rumpun.py on the CURRENT repo file
/mnt/data/work/rumpun/tests/test_rumpun.py (read it first; keep all 31
existing tests passing).

The module lands at integration (spec; author against exactly this):
  audit.run_audit(root: Path, last_n: int = 10) -> Path
  - reads musim/s*.yaml (last n by number) and rimba/<sid>/ artifacts;
  - appends akar record id "audit-<next_index>" (1 + count of audit-* files
    in akar/); returns the record path;
  - body contains per-phase liveness lines "wrote its artifact in K of N";
  - a declared phase with 0 artifacts across >= 2 rimba seasons yields a
    candidate line "exercise or trim";
  - seasons whose _season/state.json status is stopped_stall yield a
    recurrence finding; >= 2 yields a "re-size stall/budget" candidate;
  - audit.AuditError wraps akar duplicate-id errors.

Add, at minimum (tmp project builder: .rumpun with rumpun.yaml manual stage,
musim/s1.yaml + s2.yaml (two-phase pipeline: execute writes results.jsonl,
evaluate writes verdicts.jsonl), akar/ dir; rimba/s1 with results.jsonl +
verdicts.jsonl + _season/state.json (status completed); rimba/s2 EMPTY ->
its phases are dead):
1. run_audit returns a path under akar/ whose text contains "audit-1".
2. Second run_audit on the same root writes "audit-2".
3. A season with no rimba dir appears as a dead-phase finding (text names
   the phase and cites the season id).
4. stopped_stall state in one season produces the stall finding but NOT the
   re-size candidate; two such seasons produce it.
5. run_audit never modifies musim/ or rimba/ (compare dir snapshots before
   and after).

Collab lane (protocol v2, NON-BLOCKING): post kind=start, kind=policy,
kind=done via lane_tool.py from the env vars. Never wait on w1.

Rules: pytest only; no skips; no mocks. ruff clean, line-length 100,
py3.10+. notes.md: what you added, what you left out.
