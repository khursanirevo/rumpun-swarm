# s31 w1 — render-on-change for the watcher's state hook

## Verdict first

Gate landed per spec. One existing test cannot stay green under it — measured, not
assumed — and needs a tests-side fix at merge (w2 owns tests/):

- `test_watch_cycle_refreshes_index_hook` asserts `len(calls) >= 2` for a sleep-3
  stub. Measured: that stub's season state.json is byte-static across all 5 watch
  cycles, and `render_index` reads persisted state only (report.py `read_persisted_status`,
  no /proc). So the gate's one render is the only non-identical render that exists;
  a second render redraws the same page — the audited waste (audit-19: ~1600
  identical renders) itself. The assertion codifies the per-cycle rendering being
  removed. See "Reconciliation" for the tests-side fix.

## What landed (engine.py)

- `_state_digest(root, sid)`: sha256 of persisted state.json bytes, one read.
- Watcher loop: closure-held `last_render_digest` (single-season scope). Hook
  renders only when the digest differs from the previous render's. First cycle
  always renders (cache starts None).
- Hook render log downgraded to `logger.debug`; per-render INFO stays in the
  report functions. Digest read OSError: logged, render skipped, cache held.
  Hook-failure swallow (`state hook failed (ignored)`) unchanged.
- CLI finally-block terminal render untouched (unconditional). Zero new polling:
  the hash read rides the existing cycle.
- Change set: 3 regions; `diff -u` against the repo file checked. Merge-ready
  copy at this workspace's `engine.py`; patched tree at `scratch/src/`.

## Verification (all ✅ measured this session)

| Check | Result |
|---|---|
| e1 probe: original engine, sleep-3 stub | 5 cycles, 1 distinct digest; gate would render 1 |
| Repro A: mid-run byte rewrite re-renders | PASS: 2 renders (cycle 1 + first cycle after the 1.5s rewrite) |
| Repro B: byte-static sleep-6 stub, 6+ cycles | PASS: exactly 1 render across 6.01s watch |
| Suite vs patched copies (142 tests) | 1 failed, 139 passed, 2 skipped, 45.0s |
| The 1 failure | the hook test above: `assert 1 >= 2` — intended red, measured reason |
| The 2 skips | s15 real-stream fixtures absent from the clone; with s15 symlinked: 13/13 stream tests pass |
| `test_state_hook_failure_never_kills_watcher` | green in every run |
| ruff --no-respect-gitignore (engine + 3 scripts) | clean |

Reproduce (from this workspace; absolute paths for the pytest run):

```
python3 scratch/e1_probe.py            # original engine: digest truth per cycle
python3 scratch/repro_a_bytes_change.py
python3 scratch/repro_b_bytes_static.py
PYTHONPATH=$PWD/scratch/src <venv>/bin/python -m pytest $PWD/scratch/tests/test_rumpun.py -q -rs
```

Scratch fidelity for the suite run: `tools/` copied unmodified, `.rumpun/akar/evidence`
and `.rumpun/rimba/s15` symlinked from the repo. Real pytest exit lives in the
`suite exit=` line of `scratch/suite.log` (the background wrapper always exits 0).

## The conflict, precisely

- All season state.json writes precede the watch loop (grep: 6 `_save_state`
  call sites, all outside it) and none exists inside it; a quiet stub never
  triggers one mid-watch. Digests across cycles: 5 identical (e1 probe).
- Therefore `calls >= 2` is unsatisfiable under any faithful hash gate without
  redrawing identical pages. w2's pin 1 ("state bytes never change renders
  exactly ONCE") contradicts the existing test for the same stub shape; pins
  1-3 are green against this patch (pin 1 ≡ repro B, pin 2 ≡ repro A, pin 3 ≡
  both scripts' first-cycle render).

## Reconciliation (w2 / harness merge)

Smallest tests-side fix that keeps the test's intent (hook refreshes the index
mid-season): relax the old assertion to `len(calls) >= 1` and pin the second
render the pin-2 way — rewrite state.json between cycles, then assert
`len(calls) >= 2`. Alternative: `>= 1` alone, with w2's pin 2 owning the
re-render property.

## Artifacts

- `engine.py` — merge-ready patched copy (byte-identical to `scratch/src/rumpun/engine.py`)
- `scratch/e1_probe.py`, `scratch/repro_a_bytes_change.py`, `scratch/repro_b_bytes_static.py` + `.log` files
- `scratch/suite.log` — final suite record
