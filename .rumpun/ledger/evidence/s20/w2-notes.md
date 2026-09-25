# s20 w2 — H8 rejected/rollback lifecycle in evolve.py; H5/H8/H9 pinned spec-first

## Anchors

- Codex review: `.rumpun/akar/evidence/codex-review-2026-09-14/review-full.txt`
  — H5 at :6514, H8 at :6520, H9 at :6522 (repeated in the summary at
  :6573/:6579/:6581).
- w2 evolve.py copy: `.rumpun/rimba/s20/w2/evolve.py` — hunks vs the repo
  file (diff-measured): module docstring stop-first line (9,10c9,10);
  `from rumpun import akar, engine, lint, yamlio` (19c19); `_reject_record`
  added (140a141,153); apply docstring rewrite (142c155, 144,146c157,162);
  apply lifecycle gate (147a164,172); rollback docstring rewrite (256c281,287
  + 259,267c290,299); stop-active-first block (279a312,318). Parses; ruff
  clean.
- Tests: `tests/test_rumpun.py` — additions-only vs the repo file: 0 removed,
  297 added (diff-measured). 6 new tests.
- New test anchors (workspace file): section header :2070; fixtures
  RUMPUN_YAML_H5 :2096, SEASON_BUDGET :2104, RUMPUN_YAML_BUDGET :2140;
  H8 pins: apply-refuses :2150, apply-control :2158, rollback-active :2166,
  start-refusal :2245; H5 pin :2260; H9 pin :2301.

## Contracts as pinned / landed

**H8 apply gate (my evolve.py):** apply loads the draft (`_load_draft`:
parseable YAML with an s<N> id) and refuses when
`akar.find_record(root, "reject-<sid>")` resolves — exact declared-id
resolution, the s19 H7 mechanism, so a substring id never matches. The
refusal precedes lint. A clean season still applies; another sid's reject
record never blocks (control test).

**H8 rollback (my evolve.py):** rollback_season reads
rimba/<sid>/_season/state.json via engine._load_state; status running →
engine.stop_season(root, sid) first, in the caller's thread (an
engine.EngineError wraps into EvolveError), then move + record. The call
order is pinned as exactly ["stop", "record"] via spies on
engine.stop_season and akar.append_record; the behavioral leg asserts
stopped_operator, both stubs dead, the yaml moved, and the record body.

**H8 start refusal (w1's engine.py spec):** start_season refuses a yaml
whose resolved parent directory is not musim/ — resolve the yaml path,
require parent == musim/. Drafts apply via evolve, not start, so musim/ is
the only canonical placement. Pin: reject_draft moves the file to
musim/rejected/ and records reject-s1; starting the moved file raises
EngineError and creates no season state.

**H5 spec for w1:** keep the EngineError raise. Pin invariant: any stub that
ran must be registered (its workspace state.json exists) and dead after the
abort; a never-admitted stub must never have run. Both fix shapes pass:
(a) preflight every route before any spawn, or (b) terminate registered
children on abort. Fixture: two benih, w2's route absent from routes; marker
stub for w1 (touch marker; sleep 120).

**H9 spec for w1:** per-agent deadline = its own budget.minutes * 60 from
its own started_at. Fixture: short = minutes 0.05 (3s) sleeping far past it;
long = minutes 10 finishing in ~8s. Pin: the season settles inside a 45s
window, short's snap is "terminated" and its process dead, long's snap is
"exited 0" with its done marker, season status != running. Today the season
deadline is max(budgets) = 600s, so nothing stops short in the window and
start_season never settles — that timeout is the red.

## Measured red set (current repo code + this test file, scratch tree)

Scratch tree: repo `src/` + this test file. Command:
`PYTHONPATH=src python -m pytest tests/test_rumpun.py -q -p no:cacheprovider`.
Final warm red run: `5 failed, 95 passed`, exit 1 (a cold run can add the L2
dual-start transient — see watch item).

| expected red | evidence (warm red run) |
|---|---|
| `test_apply_refuses_rejected_season` (H8) | "Failed: DID NOT RAISE EvolveError" — apply gated on lint only |
| `test_rollback_active_season_stops_agents_before_record` (H8) | `assert not True` where `engine._alive(pid, proc_start)` is True — the stub outlived the rollback and the watcher never settled |
| `test_start_refuses_rejected_season_yaml` (H8) | "Failed: DID NOT RAISE EngineError" — the rejected file started |
| `test_start_error_mid_spawn_leaves_no_live_untracked_child` (H5) | `engine._alive(pid, proc_start)` is True — w1 outlived the startup abort |
| `test_agent_budget_deadline_is_per_agent` (H9) | "Failed: season never settled in 45s: the short-budget agent was not terminated at its own deadline" |

The control `test_apply_passes_clean_season_without_reject_record` passes
against current code — regression guard, not a red.

## Verification (all measured this session)

- Baseline: repo tree, `94 passed`, exit 0, measured twice (session start
  22.11s; after all edits 23.50s).
- Additions-only proof: diff repo vs workspace test file → 0 removed,
  297 added.
- evolve.py patch proof: diff repo vs workspace copy → the hunks above,
  nothing else. The diff gate caught three transcription defects in my
  first draft (a `next_id: shape` annotation typo, an out-of-scope
  musim.mkdir replacing the missing-musim error, a duplicated log line);
  all fixed pre-delivery.
- Red tree (repo code + new tests), warm, final file: `5 failed,
  95 passed` — exactly the table; every baseline test passes.
- Green tree (workspace evolve.py + new tests), warm, final file:
  `3 failed, 97 passed` — my two H8 pins plus the control pass with my
  evolve.py; the reds are exactly w1's engine pins (start-refusal, H5, H9).
- Ruff: `ruff check --no-respect-gitignore --line-length 100` on both
  workspace files → All checks passed. The flag is required: rimba/ is
  gitignored, a bare run checks zero files.

## L2 watch item (measured today)

`test_dual_start_single_spawner` (review L2, scheduler-timing dependent)
failed in 4 of 7 full-suite runs today (red-cold, green-cold, green-warm,
red-warm2) and 1 of 3 solo runs, always the same signature: starter 2 exits
1 with "ERROR season s1 already finished (completed); use a fresh id" —
starter 2 arrives after starter 1 completed the season. It hit in both
trees, with and without my evolve.py, so it is not caused by this season's
patches; it flakes harder than s19's cold-only pattern, likely under load.
It is a known review finding with a known fix shape (hold the first starter
inside the spawn transaction behind an explicit barrier, review L2).
Recommend landing the L2 barrier fix; until then, scratch gate runs treat
it as a flake candidate and re-run before recording.

## Handoff to w1 / harness

- evolve.py: apply the workspace copy (merge-ready; hunks above).
- engine.py: land H8 start refusal (placement gate: resolve the yaml,
  require parent == musim/), H5 (no live untracked child after a startup
  abort; preflight and terminate-on-abort both pass the pin), and H9
  (per-agent budgets; the pin asserts short=terminated, long=exited 0, the
  season settles; status word at season level is w1's choice).
- After w1 lands and the harness merges: repo tree expected `100 passed`
  (94 kept + 6 new).
