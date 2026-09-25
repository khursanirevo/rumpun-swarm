# s38 w1 — the checker verifies the loop LOOPING

## What was built

Steps 7–11 added to the s37 cold-start checker; the workspace copy is
`tools/coldstart_check.py` (repo's `tools/coldstart_check.py` untouched).

- Step 7 — read-only recheck that the step-6 audit landed exactly one
  `audit-1` record with its id line in akar/.
- Step 8 — `rumpun evolve plan .rumpun/musim/s1.yaml`; PASS requires
  musim/s2.yaml on disk with `id: s2` and `parent: s1`.
- Step 9 — minimal s2 edit, then `rumpun lint .rumpun/musim/s2.yaml` must
  exit 0. The edit: fill the four `primary_change` band fields the skeleton
  ships empty (lint requires them for a parented season), add one evidence
  citation `akar:audit-1@<digest>`, and keep the s1-style glm-5.2/fable →
  stub route substitution as a drift guard (evolve copies the parent benih
  verbatim, so routes already carry over as stub).
- Step 10 — `rumpun season start .rumpun/musim/s2.yaml --json`: completed,
  every benih exited 0.
- Step 11 — `rumpun harvest s2 --verdict WIN`: one `s2-harvest` akar record
  with id line, plus the (s2, WIN) row in rimba/s2/verdicts.jsonl.

Steps 4/5 were parameterized (sid, step number, implies line) so s2 reuses
the s1 path verbatim; s1's recorded implies string is unchanged from s37.
The summary count is derived from the list: `11/11 steps PASS`.

## Decision notes

- The audit-1 citation digest is recomputed in the checker the same way
  `lint._citation_resolves` does it (body = lines[4:-1] joined, sha256 of
  the utf-8 bytes). A wrong digest fails lint, which is the loop's own
  gate — the citation is checked for real, not decorated.
- Step 9's lint run is inside step 9 per the task text ("edited ... and
  rumpun lint passes on it"). First failure anywhere still exits nonzero;
  the temp dir is printed at the end either way.
- No campaign state touched: the run lives in its own temp dir; the repo's
  `.rumpun` ledger was only read (akar records listed below).

## Verification (all ✅ measured this session)

- Checker: 11/11 steps PASS, exit 0. Full log: `runner.out` in this
  workspace. Temp dir kept for inspection:
  `/mnt/data/tmp/rumpun-coldstart-e2tvpudb` — confirmed on disk: akar has
  `2026-09-15_audit-1.md`, `2026-09-15_s1-harvest.md`,
  `2026-09-15_s2-harvest.md`; musim/s2.yaml present with the filled band,
  the audit-1 citation, and both benih on `route: stub`; rimba/s2/ holds
  a1/a2 workspaces with results.jsonl, verdicts.jsonl, report.html,
  _season/state.json.
- Ruff: `ruff check --no-respect-gitignore tools/coldstart_check.py` —
  All checks passed (pyproject config: line-length 100, py310). The
  `--no-respect-gitignore` flag is required under rimba/ (ruff otherwise
  checks zero files there).
- Suite: `pytest -q` at the repo root — 178 passed in 61.54s, exit 0
  (full output: `pytest.out` in this workspace).
