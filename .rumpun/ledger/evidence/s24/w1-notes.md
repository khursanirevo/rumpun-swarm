# s24 w1 notes — content-based stall progress + harvest band/observed flags

Date: 2026-09-15. Workspace: `.rumpun/rimba/s24/w1/`. All writes stayed in this
workspace (`scratch/base`, `scratch/patched`, `scratch/repro`, this file); the
repo tree was not touched. Diff vs base: `scratch/repro/diff_base_patched.txt`
(read back after capture). Only `src/rumpun/engine.py` and `src/rumpun/cli.py`
changed; no forbidden file was opened for write.

## Result

Both fixes landed in `scratch/patched` and are verified there.

| Check | Result |
|---|---|
| Repro 1 (stall fates differ, real engine e2e) | ✅ patched: toucher stalls 3.2s, appender 6.2s; base: toucher survives to budget (the M10 defeat) |
| Repro 2 (harvest --band/--observed) | ✅ patched: row carries both; no flags: both stay `""`; base: `--band` rejected exit 2 |
| Suite against patched copies | ✅ 117 passed in 31.24s, exit 0 (solo run) |
| ruff (line-length 100, py310) | ✅ engine.py, cli.py, both repro scripts: 0 findings |

## Fix 1 — content-based stall progress (engine.py)

- `log_hist: dict[str, tuple[int, float]]` in the `start_season` watcher:
  agent name -> (last-seen `agent.log` byte size, time that size last grew).
  Updated once per cycle inside the existing per-live-agent loop; the stat
  rides the existing cycle, zero new polling.
- `_agents_snaps(root, sid, stall_s, log_hist=None)` threads history;
  `_agent_snap(ws, stall_s, last_size=None, last_progress=None)` applies it:
  grown size -> progress now; unchanged size -> no progress whatever mtime
  says; quiet -> progress time holds at the last growth; missing log ->
  `started_at` floor (kept per the brief).
- History-less callers (`read_status`, `stop_season`, `_finalize`, first
  watcher cycle, reattach) keep the s15 mtime estimate. This is deliberate:
  the stall DECISION runs in the watcher, where history exists, so the
  enforcement site is content-based; single-shot callers have no cross-cycle
  truth, and the mtime estimate keeps both existing pins green by design:
  `test_agent_snap_stall_tracks_log_progress_not_runtime` (s15) and
  `test_agent_snap_mtime_only_touch_counts_as_progress` (s23 M10 pin). The
  M10 pin's docstring stays truthful: it pins `_agent_snap`'s history-less
  contract; the trade-off is closed at the site that decides stalls.
- The code-site comment now describes the content rule; the module docstring
  gained the one-line rule statement. audit-12 (stall recurrence 2/9: s15,
  s20) and akar `stall-rule-fired-on-runtime` are the cited records; the s15
  record's fix is upgraded from mtime proxy to byte-size growth.

Brief discrepancy, stated: the brief's parenthetical says the toucher
"(stays running until budget)". That is the BASE fate, and the repro shows
it. Under the fixed rule the toucher's fate is `stopped_stall`: touch-only
activity is the defect the fix removes. Both fates are recorded above.

Residual limitation, kept honest in the code comment: an agent that appends
bytes (heartbeat lines) without doing work still defeats the rule —
byte growth is the signal, content is not judged. DESIGN 13's "identical log
lines do not count" is narrower than this rule; closing that needs
content-hashed progress events (the P25/P36 candidate), not a size check.

## Fix 2 — harvest --band / --observed (cli.py)

- `harvest` gains optional `--band` and `--observed` (default `""`), passed
  through to `harvest_season`, whose signature already carried them since
  s21. Help text names both; the CLI module docstring states the fix. Empty
  defaults keep every existing row shape and call site unchanged.

## Evidence (all captured under `scratch/repro/`)

Repro 1 — `repro_stall_fates.py`, real `engine.start_season`, stub routes,
stall 3s, budget 15s. Outputs: `out_stall_{base,patched}/results.json`.

| scenario | tree | status | duration | agent |
|---|---|---|---|---|
| sa toucher (`touch agent.log` forever) | base | completed | 15.2s | terminated_budget=true |
| sa toucher | patched | stopped_stall | 3.2s | terminated |
| sb appender (appends ~3s, then quiet) | base | stopped_stall | 6.2s | terminated |
| sb appender | patched | stopped_stall | 6.2s | terminated |

Fates differ and match the rule: the toucher loses its mtime protection
(3.2s, before budget); the appender keeps its grace window and stalls only
past stall_s since its last growth (6.2s, unchanged from base — no
regression on real progress).

Repro 2 — `repro_harvest_flags.py`, real `cli.main(["harvest", ...])`.
Outputs: `out_harvest_{base,patched}/results.json`.

- patched, sh1 with `--band "WIN if p95 <= 0.42" --observed "p95 = 0.41"`:
  row carries `band: "WIN if p95 <= 0.42"`, `observed: "p95 = 0.41"`.
- patched, sh2 without flags: `band: ""`, `observed: ""` (backward compat).
- base, sh1: argparse `unrecognized arguments: --band ...` -> exit 2, no row
  (the red check); sh2: same empty-fields row as patched.

Suite: `PYTHONPATH=src python3 -m pytest tests/ -q` in `scratch/patched` ->
`117 passed in 31.24s`, exit 0 (`out_suite_patched.txt`). Solo run per the
season scratch discipline.

Two script defects were caught and fixed during the run, both in the repro
tooling, none in the patch: a chdir-before-resolve path bug, and a missing
row crashing the base-run readback instead of recording the red. Outputs
above are from the fixed script's final runs.

## Merge notes for the harness

- Files: `src/rumpun/engine.py`, `src/rumpun/cli.py` only.
- No test pins were touched (w2 owns them). The two stall pins stay green
  against the patch unmodified, as measured above.
- s24's own season config uses the default 45-minute stall; the new rule
  only changes fates for touched-but-not-grown logs, so live watcher
  behavior for silent logs is unchanged (they already floored at
  started_at under the mtime rule).
