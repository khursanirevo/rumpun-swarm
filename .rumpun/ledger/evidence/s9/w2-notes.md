# s9 w2 — spec-first tests for evolve rollback

Deliverables in this workspace only; nothing outside it touched.

| file | what it is |
|---|---|
| test_rumpun.py | repo tests/test_rumpun.py verbatim + one docstring paragraph + 7 rollback tests |
| lane_tool.py | posts/reads build-lane events via RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK |
| notes.md | this file |

## Added — 7 tests under `# --- evolve rollback (w2 s9 scope, spec-first) ---`

| test | spec line it pins |
|---|---|
| test_rollback_season_moves_and_records | original yaml gone; musim/rejected/<sid>.yaml holds the season byte-identical; the return value is the akar record (parent == root/akar); record text contains rollback-<sid>, rollback_to_last_good, git revert |
| test_rollback_season_missing_raises | musim/<sid>.yaml absent -> EvolveError whose message says "reject" |
| test_rollback_season_bad_sid_raises[x9] | sid not matching s<N> -> EvolveError |
| test_rollback_season_bad_sid_raises[season1] | same |
| test_rollback_season_twice_raises | second rollback of a moved sid -> EvolveError |
| test_rollback_season_collision_raises | pre-existing musim/rejected/<sid>.yaml -> EvolveError, and the season survives (no destructive half-move) |
| test_rollback_season_akar_error_wraps | rollback-<sid> record id already declared -> AkarError surfaces as EvolveError |

Beyond the four required tests: collision and AkarError-wrap, both named in
the spec but outside the minimum list.

## Left out

- No CLI e2e (`python -m rumpun evolve rollback`): the spec is the library
  function; verb wiring is w1's scope.
- No assertion on record body wording beyond the two required strings.
- No test for a missing musim/ directory: same EvolveError branch as a
  missing file.
- No concurrency test: rollback is an operator action, single writer.
- No pin on move-vs-append ordering: the wrap test asserts only the error
  type, so it passes under either order.

## Verification — all measured, 2026-09-14

- `ruff check` on both .py files: clean (line-length 100, py310 target).
- `diff tests/test_rumpun.py` vs the workspace copy: only the docstring
  paragraph and the new section differ; the existing 24 tests are
  byte-identical.
- `pytest .rumpun/rimba/s9/w2/test_rumpun.py -q`: 24 passed, 7 failed.
  All 7 failures are `AttributeError: module 'rumpun.evolve' has no
  attribute 'rollback_season'` — the expected pre-integration red. The
  suite reads 31/31 once w1's implementation lands.
- Lane: start/policy/done posted (seq 0, 3, 4); lane read back in full
  afterwards. Never waited on w1.

## Lane observations

w1 (seq 1–2): rollback takes SID, mirrors reject, verb never runs git —
consistent with this spec. The untracked musim/s10.yaml in the repo is
w1's draft artifact; untouched.
