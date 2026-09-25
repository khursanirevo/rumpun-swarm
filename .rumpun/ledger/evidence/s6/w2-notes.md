# s6 w2 — process-level dual-start test for the state lock

## What shipped

| File | Content |
|---|---|
| `test_rumpun.py` | repo tests/test_rumpun.py verbatim + `test_dual_start_single_spawner` |
| `lane_tool.py` | collab v2 evidence tool (env-driven lane, never waits on w1) |
| `notes.md` | this file |

## What the test proves

`test_dual_start_single_spawner` builds a scratch project (`<tmp>/proj/.rumpun`:
manual autonomy, three invariants, route `glm: "cat {prompt} > /dev/null"`,
season s1 with two benih `alpha`/`beta`, budget 1 minute each) and launches
two `python -m rumpun season start <yaml>` subprocesses back-to-back.

Mechanism under test (engine.py `start_season`): one `_state_lock` flock spans
state load, the finished check, the initial save, and the whole per-benih spawn
loop. Starter 2 blocks on the flock, then reads the fully spawned state and
reattaches — both names already in `spawned`, so both `continue` — instead of
spawning again.

Assertions, and what each rules out:

| Assertion | Rules out |
|---|---|
| both starters returncode 0 | starter 2 crashed on a torn/lost state, or hit the `already finished` error path |
| final `state.json` parses | torn write from unsynchronized starters |
| status `completed` | one starter finalized into a non-terminal or contradictory state |
| `spawned` has `alpha` and `beta` each exactly once, no extras | a second spawn cycle appending or clobbering the map |
| both per-agent `state.json` exist | workspaces lost to interleaved creation |
| `"spawned alpha"` appears in exactly one stderr stream | a double spawn — each spawn logs one line, so a re-spawn emits a second |

The spawn-log count is the direct double-spawn witness: the map alone cannot
show it, because JSON object keys cannot repeat (a re-spawner overwrites the
same key). The log line is unconditional per spawn in `start_season`.

## Verification (✅ verified real)

- `uv run pytest .rumpun/rimba/s6/w2/test_rumpun.py -q` → **20 passed** (19
  existing kept green, 1 new; baseline repo run before changes: 19 passed).
- Dual-start test alone, 5 consecutive runs → 5 × `1 passed` (0.2–1.2s each).
- `uv run ruff check` on both files → clean (repo config: line-length 100,
  target py310, select E,F,I,UP,B,SIM,RUF).
- Lane events posted seq 0 (`start`), 1 (`policy`), then `done` — from `w2`,
  via `lane_tool.py` under the engine-exported env pair.

## Timing caveats

- **Overlap requirement.** Starter 2 must reach the flock while the season is
  still `running`. Back-to-back `Popen`s keep this: both starters do identical
  interpreter + lint startup, and starter 1 holds the lock only ~100ms longer
  (the spawn cycle), so starter 2 arrives mid-hold and blocks. If starter 2
  were ever delayed past starter 1's full exit, the engine by design answers
  `already finished (completed); use a fresh id` and exits 1 — the test asserts
  the overlapping-start contract, not post-completion idempotence.
- **Poll granularity.** The watch loop polls every 1s; the `cat` agents exit in
  milliseconds, so terminal detection lands on the first or second poll. That
  spread is the 0.2s vs 1.2s runtime difference across runs; it does not affect
  the assertions.
- **Finalize race.** Both starters can reach `_finalize`; it is first-writer-wins
  under the same flock, so the final `state.json` is one completed write either
  way. Which starter writes it is scheduling-dependent and unasserted.
- **What this test does not prove.** A hypothetical lock-free engine could pass
  by luck of scheduling (final state may still look intact after a lost
  update). The spawn-log assertion catches a double spawn whenever one occurs
  in that window; repeated runs (5/5 here) raise confidence, not proof to 1.

## Timing observed (✅ verified real, this machine)

| Item | Value |
|---|---|
| full workspace suite (20 tests) | 1.22s |
| dual-start test alone, min / max of 5 | 0.22s / 1.19s |
| communicate timeout budget | 180s per starter (never close to hit) |
