# s22 w1 notes — M1 deterministic running-season renders + M5 exit honesty

Date: 2026-09-15. Workspace: `.rumpun/rimba/s22/w1/`. All writes stayed in
this workspace; nothing in the repo tree was touched.

## What changed (patched copies in scratch/patched, diffed vs scratch/base)

- `src/rumpun/engine.py`
  - M5: `_finalize` reclassifies the all-terminal path: when the recorded
    status is "completed" and any final snap is "failed" or "crashed", the
    recorded status becomes "failed". Rule-stopped seasons
    (stopped_stall, stopped_operator) keep their rule status; the agents
    map carries per-agent truth. "terminated" stays an engine stop, not an
    agent failure (H9 contract preserved).
  - M1/M5 support: `read_persisted_status(root, sid)` — the stored state
    exactly as recorded, no /proc reads, no clock; `read_status` is now
    read_persisted_status plus the live recompute for running seasons, so
    the cli and harvest keep their live surface (cli untouched for M1).
  - M5: `status_exit_code(status)` — the documented mapping:
    0 for completed / stopped_operator / running; 1 for failed /
    stopped_stall / stopped_budget / anything unknown (an unrecognized
    terminal state must not look healthy). stopped_budget has no current
    producer; it stays in the map because the report palette knows it.
- `src/rumpun/report.py`
  - M1: every view renders from persisted state only — all five read
    sites (_strip_tally, _campaign_section, render_index x2,
    render_report) now use read_persisted_status; no /proc reads inside a
    render. A RUNNING season page renders byte-identically from identical
    state.json bytes; the landing page's live freshness stays with the
    state hook's re-renders (cli wiring unchanged).
  - M1: `_workspace_files` walks `sorted(rglob)` — deterministic link
    order. agent.log is still deliberately linked first (the agent's full
    stream), deliverables sort after it.
  - M1: render_report reads state.json bytes ONCE; the footer hash and the
    page parse the same bytes, so the self-identifying hash covers exactly
    what the page rendered from. A missing state.json raises EngineError
    (was FileNotFoundError before).
  - Consequence, recorded honestly: a RUNNING season's page shows the
    persisted fields (status, started_at, spawned set) and no agent snaps
    — snaps land in state.json at finalize, and rendering anything not in
    the hashed bytes would reintroduce the defect. The landing page keeps
    the "building right now" line from persisted started_at.
- `src/rumpun/cli.py` (minimal + documented, allowed for the exit mapping)
  - M5: `_season_exit(state)` helper returns `engine.status_exit_code`.
    The four single-season verbs start / stop / status / show return it.
    `season list` stays informational (exit 0) — it prints all seasons.
  - No other cli change; lint/gates/logging untouched.

No additive "exit_honest" state field was needed: the recorded status
stays inside the vocabulary akar/report/audit already read (audit's F2
reads stopped_stall; harvest reads terminal statuses; report palette knows
every status value). Unknown statuses map to exit 1 in the verb mapping
only, so no state consumer can see a value it does not know.

## Evidence (captured in scratch/repro/out_*.txt)

- `repro_m1_deterministic.py <copy>` — running-season fixture rendered
  twice under two monkeypatched time.time values:
  - patched: GREEN 4/4 — page bytes identical across clocks, index bytes
    identical, footer sha256[:12] equals the hashed state.json bytes,
    persisted status shown (out_m1_det_patched.txt, EXIT=0).
  - base (pre-fix): RED — season page bytes drift across clocks
    (out_m1_det_base.txt, EXIT=1). The landing page was already
    deterministic pre-fix (it never rendered agent seconds); the defect
    bit the season page.
- `repro_m1_sorted_links.py <copy>` — workspace files created in reverse
  alphabetical order, rendered link order asserted:
  - patched: exit 0 on 3/3 runs — agent.log first, deliverables sorted
    (out_sorted_patched_1..3.txt, out_sorted_summary.txt).
  - base: exit 1 — readdir order came back visibly unsorted
    (out_sorted_base.txt shows the unsorted list).
- `repro_m5_failed_exit.py <copy>` — 23 checks:
  - patched: GREEN 23/23, EXIT=0 (out_m5_patched.txt): finalize downgrade
    for failed/failed mix/crashed+exited; all-exited-0 and
    terminated-only stay completed (H9); stopped_operator keeps its rule
    status; the full status->exit mapping incl. unknown-status->1; e2e
    `season start` exits 1 and records "failed" with both agents failed;
    status/show/stop exit 1 on that failed season; the control season
    (agents exit 0) exits 0 end to end, status/stop exit 0.
  - base (pre-fix): RED 7/16 — both-fail and mixed seasons recorded
    "completed", `season start` exited 0 on the failed season (the
    M5 defect reproduced), no status_exit_code (Part B skipped with a
    logged SKIP, so the base run reaches the behavioral checks)
    (out_m5_base.txt, EXIT=1).
- Full suite on the patched copy: 103 passed (31.4s) — same count as the
  base run in this workspace before edits (103 passed, 31.7s).
- ruff check --no-respect-gitignore: clean on patched src/ and on the
  three repro scripts (ruff 0.16.7).
- Readback gate: `diff -rq base patched` shows exactly three changed
  source files (cli.py, engine.py, report.py); full unified diffs of all
  three were read back and reviewed after every edit round. Two
  write-corruption incidents during editing (a placeholder path and a
  lowercase literal) were caught by diff/readback and fixed before any
  gate ran; one earlier escaping bug (two read_status call sites with a
  different indent escaping a replace-all) was caught by the repro, not
  by eyeballing.

## Repro defects the repros themselves had (recorded for honesty)

- The M5 e2e first ran status/show/stop from the wrong cwd (one level
  above the project), so those verbs exited 1 on the config-not-found
  error and two "expected 1" checks passed for the wrong reason while the
  "expected 0" controls failed. Fixed (cwd = project dir) and re-run;
  stderr of every verb invocation is now logged in the captured output.
- The sorted-links expectation first assumed a fully sorted list; the
  rendered contract is agent.log first, then sorted deliverables. Fixed.

## Notes for merge

- The M5 finalize block runs inside the H1 lock (after the terminated
  reclass, before the final save) — the status write stays atomic with
  the rest of the terminal transaction.
- The e2e season runs took ~1-2s each: the watcher's first 1s cycle sees
  both agents terminal, so no timing pins were needed.
- w2 owns tests/: the three repro scripts here are repro artifacts, not
  suite tests; if pins are wanted in tests/test_rumpun.py, they port
  directly (determinism via mock.patch on time.time; finalize downgrade
  via workspace fixtures; mapping asserts).
