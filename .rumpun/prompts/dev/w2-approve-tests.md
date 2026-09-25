# Task: spec-first tests for evolve approve/reject (full test file into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s8/w2. Write ONLY
test_rumpun.py, notes.md, lane_tool.py into this workspace. Do not touch
anything outside it.

Base your test_rumpun.py on the CURRENT repo file
/mnt/data/work/rumpun/tests/test_rumpun.py (read it first; keep all 21
existing tests passing).

The functions land at integration (spec; author them against exactly this):
  evolve.approve_draft(root: Path, drafted: Path) -> Path
    - validates drafted loads and id matches s<N> (evolve.EvolveError on
      bad/missing file); appends an akar record id "approve-<sid>" via
      akar.append_record; never modifies the draft; returns the record path.
  evolve.reject_draft(root: Path, drafted: Path) -> Path
    - same validation; moves the draft to root/musim/rejected/<name>
      (EvolveError if the target exists); appends akar record "reject-<sid>"
      recording the P33 on_reject policy; returns the record path.

Add, at minimum:
1. approve_draft in a tmp project (reuse _write_proj + a filled season):
   record exists under akar/ and its text contains "approve-s2" and the
   season id; the draft file still exists and is unchanged.
2. approve_draft on a missing path raises EvolveError.
3. approve_draft on a yaml whose id is not s<N> raises EvolveError.
4. reject_draft: the original file is gone; musim/rejected/s2.yaml exists;
   the akar record text contains "reject-s2" and "rollback_to_last_good".
5. reject_draft a second time (file now missing) raises EvolveError.

Collab lane (protocol v2, NON-BLOCKING — evidence gathering only):
- RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK are exported to you.
- lane_tool.py: argv (kind, text) appends {"from": "w2", "kind": kind,
  "text": text} via rumpun.collab.append_event from the env vars; argv
  ("read", "") prints events. Post kind=start, kind=policy (the assertion
  contract you coded), kind=done. Never wait on w1.

Rules: pytest only; no skips; no mocks. ruff clean, line-length 100,
py3.10+. notes.md: what you added, what you left out.
