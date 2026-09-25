# Task: implement evolve approve + reject (full evolve.py and cli.py into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s8/w1. Write ONLY evolve.py,
cli.py, notes.md, lane_tool.py into this workspace. Do not touch anything
outside it.

Base both on the CURRENT repo files
/mnt/data/work/rumpun/src/rumpun/evolve.py and
/mnt/data/work/rumpun/src/rumpun/cli.py (read them first; keep every
behavior and all 21 tests passing; do not edit tests/).

evolve.py — two new functions (imports: add rumpun.akar):
  def approve_draft(root: Path, drafted: Path) -> Path
  - drafted must load via yamlio and its id must match s<N> (EvolveError
    otherwise, including a missing file: wrap OSError).
  - Appends an akar record via akar.append_record(root, f"approve-{sid}",
    f"season {sid} approved", body) where body states: operator approved
    the draft at autonomy stage manual; the draft's goal line; the akar
    citation that the draft's methodology.evidence names (or "none").
  - Never modifies the draft. Returns the record path.

  def reject_draft(root: Path, drafted: Path) -> Path
  - Same validation. Moves the draft to root/musim/rejected/<name> —
    create the dir; raise EvolveError if the target already exists; use
    Path.replace.
  - Appends an akar record id f"reject-{sid}" whose body records the P33
    on_reject policy (action rollback_to_last_good, pause true,
    escalate_after consecutive_rejects 2) and that manual stage means the
    operator pauses the chain.
  - Returns the record path.

cli.py:
- Replace the evolve approve/reject stubs with real verbs:
    rumpun evolve approve FILE   -> approve_draft
    rumpun evolve reject FILE    -> reject_draft
  Each logs the record path (logger.info) and returns 0. EVOLVE_STUBS keeps
  only "rollback". Docstring version note becomes v0.8.0 and the Implemented
  line gains evolve approve/reject.

Collab lane (protocol v2, NON-BLOCKING — evidence gathering only):
- RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK are exported to you.
- lane_tool.py: argv (kind, text) appends {"from": "w1", "kind": kind,
  "text": text} via rumpun.collab.append_event from the env vars; argv
  ("read", "") prints events. Post kind=start, kind=policy (the exact verb
  contract), kind=done. Never wait on w2.

Rules: stdlib only. ruff clean, line-length 100, py3.10+. notes.md: the
contract and what you flagged.
