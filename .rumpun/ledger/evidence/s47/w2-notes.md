# s47/w2 notes — the test suite's migration to the new layout

## Result

The 12 fixture-path reds: green. 9 fixed in place; 3 were already green
at baseline (the task's -rf list was stale for those three). Full suite:
210 passed, 11 failed — all 11 pre-existing at baseline, none in this
workspace's scope. ruff clean.

## Baseline (before any edit)

20 failed, 201 passed, 371s (suite-before.txt in this workspace). Nine
of the 20 are mine. The draft trio (draft_after_rejecting_latest,
draft_completed_parent_byte_identical, draft_no_state_parent_byte_
identical) ran GREEN at baseline: evolve already writes seasons/ and
ledger/ names, so they had no old-layout fixture to migrate.
## Changes (tests/test_rumpun.py only; src/ untouched)

1. _write_proj pre-creates seasons/, ledger/, runs/. Root cause of the
   seven engine/CLI reds: paths.runs_dir falls back to legacy rimba/
   when runs/ is absent, so engine state landed under rimba/ while the
   tests read runs/. Tests: dual_start, watch_cycle_scans_stream,
   stop_racing, engine_spawns_inside_workspace_cwd, rollback_active,
   agent_budget_deadline_is_per_agent, season_all_agents_failed.
2. GOLDEN_PRE_S26_BODY and GOLDEN_BODY line 1 re-captured post-s45: the
   only drift is the scope line's "musim seasons" -> "seasons"; the
   rest of both bodies is byte-identical. Capture:
   capture_golden_pre_s26.py, capture_golden_corpus.py, output under
   capture/ in this workspace; both exits 0, readbacks clean. Pins:
   audit_without_matrix_byte_identical, audit_without_corpus_flag_
   byte_identical.
## Verification

- Nine migrated tests solo by node ID: 9 passed, 23.9s, exit 0.
- Full suite, output redirected to /tmp: 210 passed, 11 failed, 94s.
- ruff check --no-respect-gitignore tests/: clean, exit 0.
- git diff shows exactly the changes above, nothing else.

## The 11 pre-existing reds (w1 owns src/, not this workspace's scope)

- 8 x test_s46_w2_plugin_pins.py: rumpun.plugin lacks resolve_prompt and
  friends; spec-first pins awaiting w1's plugin work.
- 3 x test_s43_w2_pins.py coverage findings: awaiting w1's audit patch.
- test_s38_coldstart_checker_leaves_repo_rumpun_untouched: the pin
  snapshots repo .rumpun across its ~90s checker run and catches the
  live season's own worker logs (runs/s47/w1, w2: agent.log, state.json,
  log_suite.txt) as mutation. Red at baseline and after; redirecting
  this workspace's output to /tmp did not clear it. Judge at merge with
  the season ended, or scope the snapshot past runs/sN/wN — w1's call.

The alias pins were untouched and stay green (the fallback path).
