# w1 — state lock for `engine.py` (s5, defect: lost updates on `state.json`)

## Defect

Two `rumpun season start` processes for one season id interleave writes to
`.rumpun/rimba/<sid>/_season/state.json`. tmp+replace prevents torn files, not
lost updates: each watcher keeps its own in-memory `state` and the save at the
end of each spawn-loop pass overwrites the other's `spawned` entries. Both
starters can also spawn the same benih twice (neither sees the other's entry).

## Lock design (as posted to the lane, seq 1)

- `_state_lock(root, sid)` context manager: opens `<season>/_season/state.lock`
  append-only (`"a"` recreates it if vanished, never truncates — same pattern
  as `collab.append_event`), `fcntl.flock(LOCK_EX)` before `yield`,
  `LOCK_UN` in `finally`. The lock file is never replaced, so every process
  flocks the same inode.
- `_save_state(root, sid, state, lock_file=None)`: default path flocks
  state.lock itself (open, LOCK_EX, write tmp, replace, unlock) — single
  writes. Held-lock path: caller inside `_state_lock` passes its lock file and
  the save joins that cycle. Rationale: flock is per open file description; a
  second fd on the same file from the same process would block on itself, so
  `_save_state` must take the held lock, never re-flock.
- `start_season`: one acquisition spans `_load_state`, the already-finished
  check, the initial save, and the whole spawn loop; every save in that span
  passes the held lock. A second starter blocks at the lock, then reads the
  fully spawned state and reattaches through the existing `spawned` map —
  no restructure beyond the indentation of that span.
- `_write_state` extracted (was the body of `_save_state`) so the locked and
  held-lock paths share one implementation. No behavior change.

## Scope discipline

- Collab lane env wiring (`RUMPUN_LANE_FILE` / `RUMPUN_LANE_LOCK` via
  `collab.prepare_lane`): untouched. Terminated-marker logic
  (`_terminate`, `_agent_snap` precedence exit > terminated > alive): untouched.
- `_finalize` / `stop_season`: callers unchanged; their saves now go through
  the single-write lock. Known residual, out of scope per the task:
  `_finalize`'s own load is still outside the lock, so two concurrent stop
  paths can both pass the `running` check; the existing first-writer-wins
  status check still bounds the outcome, and both writers write terminal
  states. Flagging, not fixing ("required fix, nothing else").
- Subprocess spawns happen inside the lock window: required for the
  spawned-registry atomicity; the window is file prep plus `Popen` (fast,
  bounded), and the second starter just blocks then reattaches.

## Validation — ✅ VERIFIED REAL (measured, commands below)

- ruff: `ruff check` clean on `engine.py` and `lane_tool.py`
  (line-length 100, select E,F,I,UP,B,SIM,RUF; ruff 0.14.10).
- Tests: 18 passed in 0.12s — baseline on the unmodified repo 18 passed
  (0.09s), then the full repo copy in `/tmp/rumpun-s5-w1` with this engine
  swapped into `src/rumpun/engine.py`. The probe log records
  `engine under test: /tmp/rumpun-s5-w1/src/rumpun/engine.py`, so the green
  run is against the new file, not the installed one.
- Concurrency probe (`/tmp/rumpun-s5-w1/probe_lock.py`, scratch only):
  - Phase 1: 100 read-modify-write cycles across 4 processes under one lock
    acquisition each → counter exactly 100 (lost updates would read lower).
  - Phase 2: 100 concurrent single writes via the self-lock path →
    state.json parses and equals exactly one writer's payload, no
    `state.tmp` leftovers (shared tmp name is safe because writes serialize).
  - Phase 3: two `start_season` processes racing on one season id, 2 benih →
    both exit 0, spawn-count log shows exactly 2 spawns (no duplicate benih),
    final state `completed` with `spawned == [w-a, w-b]`.
- Repo untouched: `git status --porcelain` shows only `.rumpun/musim/s6.yaml`
  untracked, not written by w1. Workspace holds exactly `engine.py`,
  `lane_tool.py`, `notes.md`.

## Collab lane (protocol v2)

- Posted `start` (seq 0) at the beginning and `policy` (seq 1) before
  finishing; `done` follows this file. No blocking wait on w2: at `done` time
  the lane carried no w2/w3 claims or questions; nothing to address here.
- `lane_tool.py` dogfoods `rumpun.collab.append_event` from the env vars;
  `read ""` prints events. Its two earlier misfires are mine (first call had
  no empty second argv; that is the spec's shape, kept).

## Files

- `engine.py` — full file, based on repo `src/rumpun/engine.py` @ HEAD.
- `lane_tool.py` — scratch-adjacent CLI, prints (allowed for this tool only).
- `notes.md` — this file.
