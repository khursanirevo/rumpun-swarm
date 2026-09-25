# s21 w1 notes — M3 unified verdict source + M11 route generator fix

## Outcome

✅ VERIFIED REAL: both defects are fixed at the generator level, all repros pass, ruff clean, and 99 of 100 tests pass. The 100th test (`test_dual_start_single_spawner`) fails identically on unpatched HEAD (control experiment below), so the failure is pre-existing on this box and outside this diff.

## What changed

### M3 — harvest.py is the single verdict writer
`src/rumpun/harvest.py`:
- `harvest_season` now ALSO appends the season-level row to
  `rimba/<sid>/verdicts.jsonl`, exact shape of the existing hand-written rows:
  `{"season", "verdict", "metric", "band", "observed", "implies"}` (that order).
- Signature: `harvest_season(root, sid, verdict, implies, band="", observed="")`.
  band/observed default empty; metric is read from `musim/<sid>.yaml` (empty when
  the file or key is absent); `--implies` maps to `implies` as before. cli.py's
  existing positional call needs no change.
- Refusal (M4, minimal form): a second harvest of a terminal season that already
  carries a season-level row raises `akar.AkarError` ("refusing second harvest")
  so cli's existing AkarError handling exits 1 cleanly. Order: verdict check ->
  state read -> refusal check -> akar record -> verdict row.
- report.py and audit.py untouched: they already read verdicts.jsonl.
- Corrupt lines in an existing verdicts.jsonl are skipped with the same reader
  contract as `report._verdict_of` (documented in `_has_season_row`).

### M11 — routes.py generates concrete commands
`src/rumpun/routes.py`:
- The generated login-route command now ends `--model claude-fable-5-1` (the
  operator's current fable id, as `DEFAULT_CLAUDE_MODEL`), overridden by
  `ANTHROPIC_DEFAULT_FABLE_MODEL` when set. No `<model>` placeholder anywhere in
  generated commands.
- gpt family: already concrete via the reviewed codex bypass route (`codex exec
  --dangerously-bypass-approvals-and-sandbox [-m <slug>]`); unchanged.
- `write_routes` runs `/bin/sh -n` on every generated command BEFORE writing the
  config and raises RoutesError on non-zero (`_sh_check`). Validation happens
  before any byte is written.
- scaffold.py needs no change: it emits `routes: {}` and write_routes fills it —
  one mechanism, no copy. Verified: no command-generation code exists in
  scaffold.py.

## Verification (✅ all measured this session)

| gate | result |
|---|---|
| ruff (line-length 100, E/F/I/UP/B/SIM/RUF) | rc=0, "All checks passed!" (`scratch/ruff-src.log`) |
| M3 repro | rc=0: no verdicts.jsonl before harvest; reader saw INVALID; harvest wrote akar + row with exact key order; metric from musim; band/observed/implies landed; second harvest refused with the refusal message; render shows "WIN — built: m3 repro goal" (`scratch/repro.log`) |
| M11 repro | rc=0: 9 routes written, zero `<model>` in the written config, concrete `--model claude-fable-5-1`, `/bin/sh -n` rc=0 independently on all 9 written commands, `_sh_check("then")` raised RoutesError (rc=2) (`scratch/repro.log`) |
| suite (cold, full) | 1 failed, 99 passed — only `test_dual_start_single_spawner` (`scratch/suite.log`) |
| suite (warm, full) | identical: 1 failed, 99 passed (`scratch/suite-warm.log`) |

Repro root: `.rumpun/rimba/s21/w1/scratch/scratch/repro-proj` (re-runnable; the
script cleans it). Repro identity check: `rumpun.__file__` under repo src/.

## The 100th test — pre-existing, control-proven

`test_dual_start_single_spawner` fails with the second starter exiting 1:
`ERROR season s1 already finished (completed); use a fresh id` (engine.py:596).
This is NOT the recorded L2 transient (which passed on immediate re-run). It is
the opposite sign: the second starter arrives after the winner's season already
completed, so the engine's terminal-start refusal fires. Control experiment
(solo, sequential, same box):

| tree | runs |
|---|---|
| patched (PYTHONPATH=src) | rc=0, rc=1 |
| unpatched HEAD 8011004 (overlay copy of the two files) | rc=1, rc=1 |

HEAD fails warm in isolation, so the instability is pre-existing; the s20-era
claim "passes on immediate re-run" no longer holds on this machine today. The
venv resolves rumpun via `__editable__.rumpun-0.11.0.pth` to src, so every run
today (including earlier typo-path runs) exercised the patched package.

## Issue draft (khursani8/rumpun — hand over, do not file)

Title: `test_dual_start_single_spawner fails when the second starter arrives after completion`

The test pins "second concurrent starter exits 0 (reattach)". The engine
(added in the s17-s20 H-series) refuses to start a terminal season
(engine.py:596). When the winner's season completes before the loser acquires
state.lock, the loser exits 1 with "already finished; use a fresh id" and the
test's rc assertion fires. The test cannot express this valid serialization
outcome. Suggested direction: accept the terminal refusal as a second valid
outcome, or make the loser reattach to a terminal season's final state. On
2026-09-14 the test failed 3 of 5 patched-tree runs and 2 of 2 HEAD runs on the
campaign box; the recorded L2 transient behavior has shifted.

## Harness notes

- cli.py:128 still applies `route["command"].replace("<model>", "fable")` at
  render time. After the generator fix it is a dead no-op; removing it requires
  a cli.py edit (w1 is barred; w2/harness cleanup candidate).
- The `--model <name>` string in the claude login route's `desc` is a
  description, not a generated command; kept intentionally.
- Three write-corruption incidents this session were caught by full readback
  and repaired before anything ran: an Edit that mangled KNOWN_CLIS in
  routes.py, a Write that corrupted five lines of scratch/repro.py, and one
  corrupted Bash command fragment. Repairs verified by readback; see memory
  verify-state-writes.
