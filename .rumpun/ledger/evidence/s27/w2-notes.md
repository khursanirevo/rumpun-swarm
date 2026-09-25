# s27 w2 — spec-first pins for tools/render_dashboard.py

Scope: 4 added pins in workspace `tests/test_rumpun.py` (additions-only vs
the repo file: diff shows 0 modified lines, 212 added; the harness merges
the tail). Baseline commit 9c5b589. w1 owns tools/render_dashboard.py;
these pins spec the batch-renderer contract w1 implements. The pins are
red against pre-s27 code by design.

## Measured red set (vs current code @ 9c5b589 — the tool does not exist)

| pin | red reason (measured) |
|---|---|
| test_render_dashboard_renders_stateful_skips_stateless | subprocess runs a missing file → error |
| test_render_dashboard_deterministic_across_runs | same |
| test_render_dashboard_imports_engine_path | missing tool file fails the pin's own guard |
| test_render_dashboard_missing_rumpun_exits_nonzero | same |

Raw: `scratch/red-set.txt` (4 failed, 129 deselected, 0.24s);
`scratch/full-pin-run.txt` (128 passed, 5 failed, 34.59s).

## Baseline and existing-suite regression

- Baseline at repo location, pre-work: `pytest tests/ -q` → **129 passed**
  in 44.22s, exit 0. Evidence: scratch/baseline-suite.txt.
- Workspace copy run: 128 passed, 5 failed. The 5: my 4 intended-red pins
  + `test_replay_matrix_has_no_regressions` (s25 pin). That pin is
  location-bound: it derives the repo from `parents[1]` of the test file,
  so from the w2 workspace it finds no tools/replay_corpus.py. Green at
  repo location (baseline-suite.txt, among the 129). Merging my tail
  restores it. Additions-only held.

## Design finding w1 must act on (measured, not assumed)

The current renderers are NOT cross-run byte-stable when rendering over
existing outputs: a season page's campaign-strip links depend on which
sibling report.html files exist at its render moment. Measured: two
batches over the pin fixture WITHOUT pre-clean differ in s1/report.html
(the first-rendered season's strip gains a link to the later sibling);
with outputs pre-cleaned before each batch, all files are byte-identical.
Evidence: `scratch/probe-fixture.txt` (script `scratch/probe_fixture.py`,
run against current src @ 9c5b589).

Contract consequence: pin 2 (two consecutive tool runs byte-identical)
forces the tool to neutralize that history — pre-clean its OWN outputs
before the render pass (rimba/<sid>/report.html for the seasons it
enumerates + rimba/index.html + rimba/discoveries/index.html), or render
order-independently. Campaign state bytes are never touched: pin 2's
snapshot also covers _season/state.json and verdicts.jsonl (must be
unchanged across runs).

## Contract decisions w1 must match (merge reconciliation points)

- CLI: argv[1] = project root (the directory containing .rumpun/), passed
  explicitly by every pin. Mirrors cli._project_root's shape.
- State rule: stateful iff `rumpun.engine.state_path(root/".rumpun", sid)
  .is_file()` — imported, not re-derived (pin 3 is the source-level pin).
- Enumeration: the fixture is compatible with either enumeration contract:
  musim/s*.yaml-driven (stateless = declared, no state) or rimba/sN-dir
  driven. s3 has both a musim yaml and a bare rimba dir. w1 picks; the
  pins hold either way. Seasons lacking a musim yaml are unpinned.
- Skip log: exactly one stderr line containing the sid AND "skip"
  (case-insensitive). Level unpinned. A summary line naming s3 breaks the
  ==1 count — one record per stateless season.
- Error path: nonzero exit AND stderr names .rumpun (logging to stderr;
  stdout print fails this pin).
- Discoveries index must exist even with no akar/ dir (the empty list
  page).
- The tool wraps report.render_report / render_index / render_discoveries
  (implied by the output-layout pins); it adds discovery, the batch loop,
  and skip handling only.

## Verification artifacts (scratch/)

- probe_fixture.py + probe-fixture.txt — spec sanity gate: pinned layout
  achievable (Q1), pre-cleaned batches byte-identical (Q2), state leak
  measured (Q3, s1/report.html)
- baseline-suite.txt — 129 passed pre-work (repo location, 44.22s)
- red-set.txt — the 4 measured red pins (4 failed, 129 deselected)
- full-pin-run.txt — full workspace file: 128 passed / 5 failed
- ruff check --no-respect-gitignore on the workspace file: All checks
  passed
