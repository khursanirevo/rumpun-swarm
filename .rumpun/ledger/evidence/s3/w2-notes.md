# w2 notes — tests/test_rumpun.py

## What this is

`test_rumpun.py`: 14 test functions (15 test items) for the rumpun core modules —
engine liveness and stop-rule internals, akar append-only records, harvest
close-out, evolve draft/apply gate, lint error findings, report document
rendering, and the collab lane contract. All fixtures are built under
`tmp_path`; no network, no repo state, no skips, no mocks.

## How to run

Land the file at the repo root as `tests/test_rumpun.py`, then:

    uv run pytest -q

The collab tests are spec-first: `from rumpun import collab` fails collection
with `ModuleNotFoundError` until w1's `src/rumpun/collab.py` lands at
integration. That is deliberate — the task forbids skips, so a missing module
must be a visible collection error, not a silently skipped test.

## Verification (evidence)

- ✅ VERIFIED: all 15 tests pass in 0.15s with w1's real `collab.py`
  (`.rumpun/rimba/s3/w1/collab.py`) preloaded as `rumpun.collab` via a /tmp
  conftest shim; the rest of the suite ran against the installed
  `src/rumpun` modules in the repo venv (pytest 9.1.1).
- ✅ VERIFIED: without the shim, collection fails on
  `ModuleNotFoundError: No module named 'rumpun.collab'` — the expected
  pre-integration state.
- ✅ VERIFIED: `ruff check --no-cache` clean under the repo config
  (line-length 100, py310 target). The `# isort: split` directive keeps the
  two mandated `from rumpun import ...` lines separate instead of letting
  isort merge them.

## Deliberately left out

- No tests for `cli.py`, `routes.py`, `scaffold.py`, `graph.py`, `yamlio.py` —
  outside this lane's scope.
- No `start_season`/`stop_season` loop tests: they spawn real subprocesses and
  poll with `time.sleep`. The state-machine internals they consume
  (`_proc_start_ticks`, `_stop_rules`, `_agent_snap`) are covered directly
  instead, which keeps the suite fast and deterministic.
- No multi-process flock race on `append_event`: two processes appending
  concurrently needs process orchestration a pytest fixture does not give
  cleanly; the single-process append/read, non-truncating `prepare_lane`, and
  corrupt-line paths pin the observable contract.
- No golden-file test of the report HTML: provenance labels and byte-level
  determinism are asserted; full markup is left to a `render_report`
  integration test later.
- `test_agent_snap` relies on `pid: 1` + a bogus `proc_start` to read as dead
  on any Linux box; it cannot assert the live/"stalled" branches without
  spawning a real process, so those stay out.
