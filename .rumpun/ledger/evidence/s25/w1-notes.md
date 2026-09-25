# s25 w1 notes — cross-season repro corpus runner

## Result (✅ measured; evidence: replay-matrix.md + logs/)

- 53 scripts discovered under `.rumpun/akar/evidence/<s*>/*.py`.
- 6-script repro corpus: **6 PASS, 0 FAIL, 0 DRIFT** on main @ c973651 (dirty worktree: this workspace + musim/s26.yaml untracked).
- 47 SKIP with per-file reasons; 0 unclassified rows.
- Verdict evidence, read from the raw logs (not transcribed):
  - s18/w1-h6-loop.py — `both-appends-succeeded in 0 of 20` (H6 fix holding; the loop is timing-dependent by design)
  - s18/w1-warn-repro.py — `PASS`, `stream_offset 419 of 419 log bytes`
  - s19/w1-repro-h2-h3.py — `RESULT: H2=PASS H3=PASS`
  - s20/w1-repro.py — all 13 checks PASS (`verdicts:` line); the script always exits 0, so the verdict reads its verdict lines
  - s22/w1-repro-m1.py — `GREEN: 4/4 checks passed`
  - s22/w1-repro-m5.py — `GREEN: 23/23 checks passed` (exercises the CLI end to end: failed season exits 1 on start/status/show/stop, control season exits 0)
- No regressions and no drift found: every archived repro of a landed fix is green against current src.

## How to rerun

```
.venv/bin/python tools/replay_corpus.py          # from this workspace
```

Needs the repo `.venv` python (corpus scripts import pyyaml via repo src).
Ruff: `ruff check --no-respect-gitignore tools/replay_corpus.py` (ruff is on
PATH, not in the project venv).

## Adapter table (runner-side only; scripts keep their meaning)

| script | normalization |
|---|---|
| s18/w1-h6-loop.py | no args; the script hardcodes the repo src path itself; PASS = `both-appends-succeeded in 0 of 20` |
| s18/w1-warn-repro.py | `PYTHONPATH=<repo>/src` (script sets no path of its own) |
| s19/w1-repro-h2-h3.py | staged copy in a temp dir with `src/` symlinked to repo src (script expects `src/` next to itself) |
| s20/w1-repro.py | argv[1] = `<repo>/src`; script always exits 0, so verdict = its `verdicts:` line with zero FAIL lines |
| s22/w1-repro-m1.py | argv[1] = repo root (script appends `/src`); exit 2 = DRIFT by its own convention; PASS = `GREEN:` |
| s22/w1-repro-m5.py | same as m1 |

The full table also lives in the runner docstring, which is the canonical copy.

## Skip taxonomy

Archived module and test copies get a name-pattern reason (engine/cli/akar/
audit/evolve/report/lint/collab copies; pytest suite copies bind to their
scratch-tree src). Three named exceptions are documented in the runner
docstring:

- `s14/calibrate_toolless.py` — one-off calibration over the rimba/ log
  snapshot, label set pinned at s14; not a repo-src repro.
- `s14/w2-make_tests.py` — test-file generator; writes a file; not a repro.
- `s16/w1-replay.py` — loads engine copies from its workspace scratch/ and
  hardcoded s15 rimba streams (now .gz) and writes results next to itself;
  fixtures moved and a run would write outside this workspace.

Safety net: a discovered script matching no table still emits an
UNCLASSIFIED row. The first run caught `s22/w2-collab.py` this way; the
collab pattern now covers numbered writer prefixes; rerun is clean.

## Runner rules honored

- Subprocess isolation: own process group, per-script timeout (60–300 s),
  killpg on timeout, staging cleanup in `finally`.
- Raw streams live only in `logs/<season>__<script>.out/.err`; the matrix
  and console carry verdict lines and error-class tokens, never script
  stderr content.
- Writes: `replay-matrix.md`, `logs/`, and this notes file stay inside the
  workspace; each corpus script was read before running and writes tempdirs
  only.
- `src/` and `tests/` untouched — w2 owns fixes; this season found none to fix.
