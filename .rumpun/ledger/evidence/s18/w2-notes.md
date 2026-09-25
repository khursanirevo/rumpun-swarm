# s18 w2 — H4 landed in lint.py; H1/H4/H6 + warning fix pinned spec-first

## Anchors

- Codex review: `.rumpun/akar/evidence/codex-review-2026-09-14/review-full.txt`
  — H1 at :6506 (`engine.py` `_finalize` races the spawn cycle), H4 at :6512
  (`lint.py` accepted `../../outside` and `_season` as benih names), H6 at
  :6516 (`akar.py` append_record duplicate check and publish are unlocked).
- w2 lint.py copy: `src/rumpun/lint.py` — H4 lands as
  `BENIH_NAME_MAX` / `BENIH_NAME_RE` / `RESERVED_BENIH_NAMES` plus
  `_benih_name_error()` at :31-62, wired into the benih loop at :280-282.
  Diff vs the repo file: two additions-only hunks, zero removed lines.
- Tests: `tests/test_rumpun.py` — additions-only vs the repo file: 0 removed,
  270 added (diff-measured). Base is the s17 salvage draft
  (`.rumpun/akar/evidence/s17/w2-test_rumpun.py`, 223 added lines, 4 test
  functions), reused with its two comment blocks reworked to s18, plus one
  new warning-transition pin.
- New test anchors: H4 reject shapes `tests/test_rumpun.py:1637` (6 cases),
  H4 accept shapes :1647 (3 cases), H6 append race :1655, H1 stop race
  :1694, warning-transition pin :1796.

## H4 spec as landed

A benih name is a workspace directory component under `rimba/<sid>/` that
the engine joins directly. Lint now rejects with an error naming the
offending name:

- empty or non-string name;
- reserved `_season` (the harness's own directory);
- length outside 1-32;
- anything off `[a-z0-9][a-z0-9_-]*` (this rejects `/`, `\`, `..`,
  leading dots; the message spells out the banned separators).

`s1`-`s17` names (`w1`, `w2`, `w3`, `alpha`, `beta`, ...) match the pattern
and stay lint-clean. The accept-shape test covers `w1`, `alpha-1`, `w2_x`.

## Warning-fix spec (for w1's engine.py)

Contract pinned at `tests/test_rumpun.py:1796`: file-tool sightings in two
separately scanned chunks must yield exactly ONE `rumpun.engine` WARNING
(caplog count). Current `engine.py` `_scan_agent_stream` (:191-195) calls
`_mark_file_tools` on every chunk holding a sighting, so the WARNING and
lane event repeat per chunk; `_mark_file_tools`' own docstring states the
intended contract ("Called only on the true transition; true is sticky, so
this never repeats"). Fix shape: emit the mark only when
`meta.get("file_tools")` is not already True, i.e. gate the
`_mark_file_tools` call on the true transition. Keep scanning and the
stream_offset advance unchanged.

## Measured red set (current repo code + this test file)

Scratch tree: repo `src/` + this test file. Command:
`PYTHONPATH=src python -m pytest tests/test_rumpun.py -q -p no:cacheprovider`.
Result: `9 failed, 71 passed, 2 skipped`, pytest exit 1.

| expected red | evidence |
|---|---|
| `test_lint_rejects_uncontained_benih_name` x6 (H4) | current lint.py has no name containment; all six shapes accepted |
| `test_akar_append_same_id_under_barrier_admits_one_writer` (H6) | red run: `assert 'body from writer zero' in '# akar record: race-1...'` — both writers admitted, writer one's body silently replaced writer zero's. Race pin: against unlocked akar.py it is LIKELY red, not always red (see green-tree note) |
| `test_stop_racing_spawn_tracks_and_kills_every_spawn` (H1) | fails the tracking invariant (`{name} ran, no marker`): the held w2 spawn lands outside the stop's ownership snapshot |
| `test_stream_warning_emits_once_across_sightings` | `assert 2 == 1` — second chunk's sighting re-emitted the WARNING |

The three H4 accept cases pass against current code (regression guard, not
a red). The 2 skips are the existing s16 real-stream replay test
(`tests/test_rumpun.py:1448` in the repo file):
`SKIPPED [2] real-stream fixture not in this clone: None` — the fixture
lives in the repo clone, not in /tmp scratch trees; that test passes in the
repo tree.

## Verification (all measured this session)

- Baseline: repo tree, 70 items `70 passed in 6.28s`, exit 0.
- Additions-only proof: `diff` repo vs w2 test file → 0 `<` lines, 270 `>`
  lines.
- lint.py patch proof: `diff` repo vs w2 copy → hunks `30a31,62` and
  `247a280,282`, nothing else.
- Red tree (repo code + new tests): `9 failed, 71 passed, 2 skipped`,
  exit 1 — the 9 are exactly the table above; all 70 baseline tests still
  pass modulo the 2 environment skips, and the 3 H4 accepts pass.
- Green tree (w2 lint.py + new tests): `2 failed, 78 passed, 2 skipped`,
  exit 1 — every H4 item passes with my lint.py copy (6 rejects + 3
  accepts). The remaining reds are H1 and the warning pin (w1's engine.py)
  and H6 (w1's akar.py). H6 passed in this run purely by scheduling luck:
  akar.py is byte-identical in both trees and the H6 pin is a race test —
  the barrier makes the unlocked window likely but not certain to be hit.
- Ruff: `ruff check --no-respect-gitignore` on both workspace files →
  `All checks passed!`, exit 0, repo line-length 100 honored. The flag is
  required because `rimba/` is gitignored (ruff would otherwise check zero
  files).
- Byte-exactness: both workspace files were read back after an Edit tool
  corruption event mid-session (one truncated return statement, one
  mangled comment); the repaired text is what the diffs above show.

## Handoff to w1 / harness

- lint.py: apply the two-hunk patch (workspace copy is merge-ready).
- engine.py: gate `_mark_file_tools` on the sticky transition (warning
  spec above) and land H1 finalize locking per review :6506.
- akar.py: land H6 append serialization per review :6516.
- After w1 lands: expected green = 80 passed, 2 skipped (the 2 skips are
  fixture-environment, not code).
