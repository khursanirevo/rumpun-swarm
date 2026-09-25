# s18 w1 — H1 finalize lock, H6 akar append lock, warning-transition fix

Deliverables in this workspace: `engine.py`, `akar.py` (patched copies; the
harness merges them over `src/rumpun/`), and this `notes.md`. The three
`*_repro/probe/loop` scripts are the verification evidence and stay with it.

## H1 — _finalize holds state.lock across the whole transaction (engine.py)

Anchors (workspace `engine.py`, line numbers from this copy):

| anchor | line | change |
|---|---|---|
| `_finalize` | ~428 | whole transaction inside `with _state_lock(root, sid) as state_lock`: terminal-state check repeats under the lock; the pre-lock read is advisory; `_save_state(root, sid, state, state_lock)` joins the held lock |
| `_finalize` kill loop | ~451 | ownership + liveness snapshot taken under the lock (`live = _agents_snaps(root, sid, 1e9)`); kill decisions use `live`, not the caller's `snaps` (those predate the lock wait and cannot see agents admitted meanwhile) |
| `_finalize_agent_stream` | ~236 | new optional `lock_file` param; write goes through `_write_agent_state_guarded`; derives its own lock when called with `None`; signature stays backward compatible |
| `_write_agent_state_guarded` | ~125 | new helper: joins a held lock or derives one (mirrors `_save_state`) |
| `start_season`, `stop_season` | — | untouched; all caller signatures unchanged; the `snaps` param is retained for signature stability and documented as no longer driving kill decisions |

Lock-order check: `_finalize` holds state.lock, then `_mark_file_tools`
acquires a lane lock via `collab.append_event`; no path acquires the lane
lock first and state.lock second, so the ordering is acyclic. `_terminate`
takes no locks. No self-deadlock: `_finalize_agent_stream` and `_save_state`
join the held fd instead of re-flocking.

Why the fresh under-lock snapshot is required, not optional: the s17 draft's
H1 pin holds the second benih inside the starter's spawn cycle while the stop
publishes. The stop's caller-side snaps were taken before the lock wait, so
without `live` the held agent escapes both the kill loop and the final
`agents` map — the exact "live and untracked" repro.

## H6 — akar append serializes duplicate-check + publication (akar.py)

Adopted from `.rumpun/akar/evidence/s17/w1-akar.py` verbatim (workspace copy
is byte-identical; `diff` empty; `py_compile` clean). Audit of the draft
passed: lock spans all three steps, tmp is pid-unique, body bytes unchanged.
One letter-of-spec note: the task said "first-use lock creation via a+ open";
the draft uses `open(lock_path, "a")` — identical create-if-missing,
never-truncate semantics, and it matches the engine `_state_lock` precedent.

| anchor | line | change |
|---|---|---|
| `_append_lock` | ~67 | exclusive flock on `akar/append.lock`; first use creates the lock file via append-mode open |
| `append_record` | ~130 | one lock spans the duplicate check (`_declared`), the `final.exists()` refusal, and the atomic publish; tmp name is pid-unique `.{final.name}.{os.getpid()}.tmp`; record layout, digest, and error surface unchanged |

`_declared` reads (then skips) `append.lock` as a no-id file: harmless, one
DEBUG line, same precedent as `directives.lock` already living in `akar/`.

## Warning-transition fix (engine.py)

| anchor | line | change |
|---|---|---|
| `_scan_agent_stream` | ~215 | `first_mark = meta.get("file_tools") is not True` gates `_mark_file_tools`; the sticky mark and the offset advance stay per-sighting; offset/mark logic otherwise untouched |

`_mark_file_tools` itself is untouched. The finalize path already early-returns
on sticky true, so its mark call was already transition-only. Lane-event
behavior rides the same gate: one event per agent, on the transition.

## Verification (all measured this session; ✅ verified real)

Module resolution probe (`probe_path.py`): PASS — the scratch tree resolves
patched engine + akar (marker symbols present, `_finalize_agent_stream`
params `[root, sid, ws, lock_file]`).

| check | result |
|---|---|
| baseline suite, unpatched repo tree | 70 passed, 0 skipped, 4.7s |
| suite, patched scratch tree (`/tmp/s18w1-scratch`, s15 fixtures copied local) | 70 passed, 0 skipped, 4.8s |
| H1 pin `test_stop_racing_spawn_tracks_and_kills_every_spawn`, patched | PASS |
| H6 pin `test_akar_append_same_id_under_barrier_admits_one_writer`, patched | PASS |
| H1 pin, unpatched tree (red-check) | FAILED — review defect reproduced ("w1 ran, no marker": the stop killed w1's stub before its marker while finalizing from a stale view) |
| H6 pin, unpatched tree (red-check) | PASSED this run — scheduler-dependent, see loop below |
| H6 old-code loop, 20 barrier runs (`h6_oldcode_loop.py`) | 1/20 runs let both appends succeed (silent replacement); several other runs hit `FileNotFoundError` tmp collisions from the shared tmp name — both signatures removed by the fix |
| warning repro, patched (`warn_repro.py`) | 1 WARNING, 1 lane event, `file_tools` True, offset 419/419 → PASS |
| warning repro, unpatched | 3 WARNINGs, 3 lane events → FAIL (the s17 live defect, quantified) |
| ruff `--no-respect-gitignore`, all 5 workspace `.py` files | All checks passed |

Commands: the exact invocations are in the script docstrings and this
session's agent.log. Patched modules for the runs came from
`PYTHONPATH=/tmp/s18w1-scratch/src` (probe guards against importing the
unpatched repo tree by accident). The three scripts are one-shot diagnostic
tools whose stdout is the evidence record; the library modules under merge
(engine.py, akar.py) log exclusively.

## Residual risks observed, not fixed (out of scope, flagged for the merge)

- An agent admitted by a starter that then crashes between the workspace
  state.json write and the season-level `spawned` save is still invisible to
  the kill loop (it iterates `state["spawned"]`). Same gap as before the
  patch; the review's repro (live starter holding the lock) is closed.
- The H6 pin is scheduler-dependent against old code: it can pass when the
  two threads do not interleave inside the old check-then-publish window.
  The fix makes exactly-one-writer true by construction, not by timing.
