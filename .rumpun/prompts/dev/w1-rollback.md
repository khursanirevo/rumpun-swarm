# Task: implement evolve rollback — the last stub (full evolve.py and cli.py into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s9/w1. Write ONLY evolve.py,
cli.py, notes.md, lane_tool.py into this workspace. Do not touch anything
outside it.

Base both on the CURRENT repo files
/mnt/data/work/rumpun/src/rumpun/evolve.py and
/mnt/data/work/rumpun/src/rumpun/cli.py (read them first; keep every
behavior and all 24 tests passing; do not edit tests/).

Semantics (harness decision, consistent with reject):
- reject contains a DRAFT (pre-apply); rollback contains an APPLIED season
  (musim/<sid>.yaml that passed apply and may have run).
- `rumpun evolve rollback <sid>` (id, not file):
  def rollback_season(root: Path, sid: str) -> Path
  - sid must match s<N> (EvolveError otherwise).
  - musim/<sid>.yaml must exist (EvolveError with a hint to use reject for
    drafts that were never applied).
  - Move it to musim/rejected/<name> (dir created; collision -> EvolveError;
    Path.replace).
  - Append akar record id rollback-<sid>, title "season <sid> rolled back",
    body: P33 on_reject containment (action rollback_to_last_good, pause
    true, escalate_after consecutive_rejects 2) plus the line that code-level
    restore is an explicit git revert by the operator (git history is the
    evolution ledger; the verb never runs git).
  - akar.AkarError (duplicate id) wraps into EvolveError. Returns the record
    path.

cli.py:
- Replace the evolve rollback stub with the real verb taking SID (not FILE).
  EVOLVE_STUBS becomes empty: drop the dict and the evolve stub loop
  (or guard with `if EVOLVE_STUBS:` — your call, state it in notes.md).
  Docstring version note v0.9.0; Implemented line gains evolve rollback.

Collab lane (protocol v2, NON-BLOCKING — evidence gathering only):
- RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK are exported to you.
- lane_tool.py: argv (kind, text) appends {"from": "w1", "kind": kind,
  "text": text} via rumpun.collab.append_event from the env vars; argv
  ("read", "") prints events. Post kind=start, kind=policy, kind=done.
  Never wait on w2.

Rules: stdlib only. ruff clean, line-length 100, py3.10+. notes.md: the
contract and what you flagged for merge.
