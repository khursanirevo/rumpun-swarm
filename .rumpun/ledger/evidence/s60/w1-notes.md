# s60 w1 — stall detection counts real progress

Season s60 worker 1. Deliverables shipped 2026-09-16.

## What shipped

- Repo `src/rumpun/engine.py` (deliverable copy in this workspace, sha256
  `ad487bb1…eba6c` on both): the stall clock now resets on three named
  progress sources, taking the newest:
  1. agent.log appended-byte growth (unchanged, scan-stamped `last_progress`),
  2. any parsed tool_use event (new: `last_tool_use` stamp + `tool_use_count`),
  3. watched workspace write growth (new: `_watched_bytes` content-byte sum,
     `ws_bytes` baseline, `last_ws_progress` stamp; engine bookkeeping
     excluded; symlinks never followed; growth-only, mtime-blind).
- `_agent_snap` takes the max over present stamps; absent stamps change
  nothing, so a dead stream with no events and no writes still floors at
  `started_at` and stalls. Genuine liveness is not weakened.
- Stop record: `_finalize` attaches `state["stall_stop"]` on `stopped_stall`
  with the rule string, `stall_s`, and per-agent `sources` (which stamps
  counted), `tool_use_count`, `ws_bytes`, `log_size`, and
  `last_progress_age_s` at the stop; one WARNING log line carries the ages.
  A stopped_stall is now auditable from the season state alone.
- Growth-only trade-off (documented at the code site): a same-size rewrite
  or a shrinking tree stamps nothing, same honesty class as the s24
  append-only rule. An externally driven workspace write stamps too; the
  rule keys on harness-observed durable progress, not authorship.

## Verification (✅ verified real)

| run | engine | season | outcome |
|---|---|---|---|
| stub | s60 patched | busy (quiet stdout, busy files) | completed, w1 exited 0, 9.1s |
| stub | s60 patched | dead (no output, no writes) | stopped_stall 6.3s, `stall_stop` recorded |
| counterfactual | HEAD copy | busy | stopped_stall 6.2s, terminated mid-write — the s59 kill, reproduced |
| counterfactual | HEAD copy | dead | stopped_stall 6.3s |

- Busy agent state readback: `ws_bytes: 9528`, `last_ws_progress` stamped
  8.05s into the 9.1s run — the clock reset on file writes, not stdout.
- Dead agent state readback: `ws_bytes: 299` baseline (prompt files), no
  stamp; stop-record `sources: {}`, age 6.2s. Dead still stalls.
- Stub tree: `stub-root/` (resolver picks `rimba/` because `runs/` is
  absent — paths.runs_dir legacy fallback; noted for the merge reader).
- Driver: `run_stub.py` (`--root/--busy/--dead/--out`), outcomes judged in
  the driver; `results-new.jsonl`, `results-old.jsonl` hold the rows.
- Targeted engine nodes (23 IDs: snap/scan/finalize/terminate/s24 pins):
  187 passed, 1 failed — `test_s38_coldstart_checker_leaves_repo_rumpun_untouched`,
  the documented in-suite environmental red; it also fails solo against a
  full pre-patch HEAD archive (`old-full/src`), so the patch is cleared.
- Full suite: pending in background; row to be amended on completion.

## Workspace map

- `engine.py` — deliverable copy of the patched repo engine (sha-verified)
- `run_stub.py`, `stub_writer.py`, `stub_dead.py` — stub agents + driver
- `stub-root/`, `stub-root-old/` — isolated season roots (evidence inside)
- `old-src/`, `old-full/` — pre-patch engine copies for the counterfactual
- `results-new.jsonl`, `results-old.jsonl` — outcome rows
