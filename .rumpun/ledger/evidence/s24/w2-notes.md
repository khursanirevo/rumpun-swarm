# s24 w2 — spec-first pins: measured red set

Tree under test: repo `main` @ 4432215, `tests/test_rumpun.py`
sha256 `9429ce81…` (unchanged after my run — repo untouched).
Deliverable: `.rumpun/rimba/s24/w2/tests/test_rumpun.py` = repo file + 139
added lines, 0 removed (additions-only proof: `scratch/additions-only.txt`).
Run 2026-09-15, `uv run pytest`, solo, warm.

## Measured red set

| pin | test | expected | measured |
|---|---|---|---|
| 1 grow | `test_agent_snap_appended_bytes_are_progress_stale_mtime` | red | RED — `assert 'stalled' == 'running'` |
| 1 touch | `test_agent_snap_touch_only_is_stalled_despite_fresh_mtime` | red | RED — `assert 'running' == 'stalled'` |
| 2 M10 comment | `test_m10_comment_references_content_based_rule` | red | RED — no M10 window names content without "mtime-based"; old s23 sentence still in engine.py |
| 3 function | `test_harvest_season_row_carries_band_and_observed` | green now | GREEN |
| 3 CLI with flags | `test_cli_harvest_passes_band_and_observed_through` | red | RED — `SystemExit: 2`, `unrecognized arguments: --band … --observed …` |
| 3 CLI without flags | `test_cli_harvest_without_flags_leaves_band_observed_empty` | green now | GREEN |

Suite totals: **4 failed, 119 passed** (123 collected = 117 kept + 6 new).
Baseline: repo `tests/test_rumpun.py` = **117 passed**, rc 0.
Ruff: `All checks passed!` (`--no-respect-gitignore`; the workspace sits in a
gitignored tree — plain ruff reports a false green there).
Artifacts: `scratch/red-base.txt`, `scratch/base-green.txt`,
`scratch/additions-only.txt`, `scratch/ruff.txt`.

## Per-test contract (what w1 builds)

1. **Content-based progress** (both stall pins). `_scan_agent_stream` stamps
   a fresh progress time into the workspace `state.json` when `agent.log`
   grew past its last observation — any consumed appended bytes count; tool
   findings are not required. `_agent_snap`'s live branch judges on that
   stamp (fallback `started_at`), never on mtime. Pins drive the existing
   seams only: one baseline scan, the log change, one more scan, then
   `_agent_snap`. No sleeps; same pattern as the s15/s23 pins (real clock,
   hour-old `started_at`, 1s window, `os.utime`).
   - Grow pin: baseline scan → append bytes → mtime forced stale (30s) →
     scan → snap must say `running`.
   - Touch pin: baseline scan → touch (fresh mtime, same bytes) → scan →
     snap must say `stalled`.
2. **M10 comment**. engine.py keeps an `M10` marker; within ±8 lines of some
   M10 line, "content" appears and "mtime-based" does not; the s23 sentence
   "touching agent.log without writing content defeats" is gone from
   engine.py entirely. Grep via `inspect`, so the comment may sit anywhere.
3. **Harvest rows**. Function level is already green (`harvest_season`
   `band`/`observed` kwargs reach the row verbatim). The red half is the
   CLI: the harvest verb gains `--band`/`--observed`, passing both through
   to `harvest_season`; without the flags both stay `""`. Fixture note:
   `_project_root` returns the `.rumpun` dir itself, so the CLI fixtures
   nest the season tree under `tmp_path/.rumpun`.

## Merge reconciliation (w1's, by design)

`s23` pin `test_agent_snap_mtime_only_touch_counts_as_progress` (repo file
tail) pins the mtime trade-off as-is — the opposite of the touch pin. After
w1's content-based patch it goes red on purpose and must be flipped/reworded
at merge. My file leaves it untouched; the flip is the s24 spec.

## Correction record

First red run measured 5 failures, not 4: the CLI-without-flags fixture
wrote the season tree at `tmp_path` instead of `tmp_path/.rumpun`
(`_project_root` returns the `.rumpun` dir). Fixture fixed, full suite
re-run, 4/119 re-measured. The first run's output file was overwritten by
the re-run; only the final measurement is kept in `scratch/`.

## Repro

    cd /mnt/data/work/rumpun
    uv run pytest .rumpun/rimba/s24/w2/tests/test_rumpun.py -q   # 4 failed, 119 passed
    uv run pytest tests/test_rumpun.py -q                        # 117 passed
    ruff check --no-respect-gitignore .rumpun/rimba/s24/w2/tests/test_rumpun.py
