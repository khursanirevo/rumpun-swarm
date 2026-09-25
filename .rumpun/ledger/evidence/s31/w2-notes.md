# s31 w2 notes — spec-first pins for render-on-change

## Verdict

Pins 1-2 red against current code for the spec reasons (render counts). Pin 3
green: the first-cycle render already holds, so it is the guard pin the gate
must keep. Real-repo suite: 142/142 green. Scratch suite with additions:
2 failed (the red pins, by design), 143 passed, 0 skipped. Ruff clean. src/
untouched by w2: the scratch engine was restored byte-identical (sha256
verified, probe clean).

## Measured red set (engine.py sha256 5477b14d09f16eb5...)

| pin | spec | measured | verdict |
|---|---|---|---|
| 1 | quiet season renders exactly once over 3+ cycles | 5 renders over ~5 cycles | RED, in-spec |
| 2 | one byte change -> exactly one re-render (total 2) | 5 renders | RED, in-spec |
| 3 | fresh watcher renders on cycle 1, before any change | first call precedes stub exit | GREEN, guard |

Tracebacks: `scratch/evidence/red-run.txt` (measured 2026-09-15, exit 1,
"2 failed, 1 passed, 142 deselected").

## Green gates

- Real repo suite: 142 passed, exit 0 (`scratch/evidence/suite-real-repo.txt`).
- Scratch suite (142 + 3 pins): 2 failed (pins 1-2, by design), 143 passed,
  0 skipped (`scratch/evidence/full-suite-current.txt`). The scratch copy
  needed `.rumpun/akar` + `.rumpun/rimba/s15` grafted for the s25 corpus
  runner and s15 stream-replay tests; without them the corpus-runner pin
  fails and the replay tests skip — copy artifacts, not regressions.
- Ruff (line-length 100, --no-respect-gitignore): exit 0
  (`scratch/evidence/ruff-run.txt`).

## Pins go green under the ratified gate (scratch-only proof)

The scratch engine was patched with w1's ratified shape (closure cache +
sha256 of persisted state.json bytes; render on first cycle, then on change;
interpreter-resolution probe TRUE before the run): pins 3/3 passed
(`scratch/evidence/green-run.txt`, exit 0). Scratch engine restored after;
sha256 re-verified identical to real src (5477b14d...), probe False.

## Integration conflict w1 and the harness must resolve

Under the ratified gate a quiet 3s season renders ONCE, so the existing
`test_watch_cycle_refreshes_index_hook` fails: its `assert len(calls) >= 2`
pins the superseded per-cycle contract. Measured: 1 render, exit 1
(`scratch/evidence/existing-hook-vs-patched.txt`). Additions-only binds w2;
that one assertion needs amending at merge (e.g. `>= 1`), or w1 must widen
the gate surface — but any surface that keeps `>= 2` on a quiet season
contradicts pin 1's `== 1`. Both cannot pass; the pins carry the ratified
contract.

## Deliverables (all under w2/ workspace)

- `scratch/repo/tests/test_rumpun.py` — the pins: one import (`threading`)
  + the s31 w2 section with 3 tests; the 142 existing tests kept
  byte-identical.
- Evidence: `scratch/evidence/{red-run,green-run,existing-hook-vs-patched,
  full-suite-current,suite-real-repo,ruff-run,runner-scratch}.txt`.
- Diagnostics kept for provenance: `scratch/probe_digest.py`,
  `scratch/probe_pin_replica.py`.

## Protocol note (why re-measured runs exist)

A first green run used `uv run pytest` from the scratch copy: the scratch
`.venv` (copied by rsync) carries console scripts with shebangs to the real
repo venv, so pytest fell through PATH to the real venv and tested the
UNPATCHED real src. Invalidated and re-measured; every result-bearing run
now goes through `scratch/repo/.venv/bin/python -m pytest` with an
interpreter-resolution probe (patched-live TRUE/FALSE as expected) before
the run. Recorded in memory (season-scratch-workflow).

## Provenance

- git HEAD 1321aae; measured 2026-09-15.
- engine.py sha256 before/after scratch runs, identical both sides:
  5477b14d09f16eb5f2264547310c781e3b1f6a8e0c9e8150b7e31843b4535410
- test file at capture: 142 existing tests + 3 pins = 145 collected.
