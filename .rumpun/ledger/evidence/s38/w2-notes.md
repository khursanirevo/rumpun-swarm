# s38 w2 — notes: spec-first pins for the loop-propagation steps

Status: ✅ pins shipped, red set measured (3 red for the spec reason + 1
green guard), 178 baseline green, and all four pins proven green against
w1's landed extended checker in a replica. All numbers below are measured;
evidence files live in `scratch/`.

## Shipped

- `tests/test_rumpun.py` (workspace copy): repo bytes + append. Prefix
  byte-identical to main (`cmp` over all 228,646 repo bytes). sha256
  `bfbc9be7…`, 239,464 bytes, 5,909 lines, 182 items collected. ruff
  0.14.10 clean (`--no-respect-gitignore`, pyproject line-length 100).
- Four s38 pins, spec-first, additions-only (178 kept):
  1. `test_s38_coldstart_checker_propagates_through_s2_harvest` — full
     run exits 0, >= 11 `\bPASS\b` markers, zero FAIL tokens, and the
     summary line reads `COLDSTART CHECK: 11/11 steps PASS` (the ratified
     extended count: s37's six + audit record, evolve plan, edit+lint s2,
     start s2, harvest s2).
  2. `test_s38_coldstart_checker_s2_artifacts_in_temp_dir` — after the
     run the printed temp dir holds musim/s2.yaml, a rimba/s2/verdicts.jsonl
     row crediting season s2 with a verdict, and exactly one akar record
     declaring `id: s2-harvest`.
  3. `test_s38_coldstart_checker_sabotaged_draft_planning_fails_naming_step`
     — with a stub draft planner active, nonzero exit, a FAIL marker, and
     a FAIL line naming the failed step (evolve plan). The stub is a
     sitecustomize.py on PYTHONPATH that replaces
     `rumpun.evolve.draft_next` with a raiser; it needs no checker
     cooperation because steps 1-7 never call draft_next and the evolve
     step is an inherited-env subprocess CLI call.
  4. `test_s38_coldstart_checker_leaves_repo_rumpun_untouched` — sha256
     map over the repo's .rumpun (minus volatile dirs, below) byte-identical
     around one full run.
- Checker invoked via subprocess with the repo venv python (`sys.executable`
  when the suite runs under .venv), `_S38_TIMEOUT_S = 180`, no wall-clock
  asserts beyond it. Missing checker = `pytest.fail`, never a skip.
- Pin 5 (regression) is the suite gate itself, measured below — not a
  suite-spawning pytest.
- Repo root via the s27 walk-up helper `_pin_repo_root()` (workspace and
  merged alike). Fragment kept at `scratch/s38-pins-fragment.py`; the
  sabotage probe + headless rehearsal at `scratch/probe_shim.py`.

## Red set (measured, against current code)

| run | result | evidence |
|---|---|---|
| repo baseline on main | 178 passed, 58.60s, exit 0 | `baseline-suite.txt` |
| the four pins, node IDs, workspace location | 3 failed, 1 passed, 18.70s, exit 1 | `red-pins.txt` |

Failure split (182 items = 178 + 4; the pins ran alone by explicit node ID
because `pytest -k` does not filter in this environment):

- Pin 1: `expected >= 11 PASS step markers (the 11-step run), found 7` —
  the 6-step checker reports 6/6 and never propagates to s2. Intended red.
- Pin 2: `no musim/s2.yaml in …/rumpun-coldstart-hg_yvbrc after the run` —
  the loop did not draft the next season. Intended red.
- Pin 3: `checker exited 0 with the stub draft planner active` — the stub
  breaks only the evolve step, which today's checker never reaches; it
  reports 6/6 and exits 0. Intended red.
- Pin 4: passed — the isolation guard holds against the current checker
  and stays armed for w1's extension.

## Green proofs (replica `scratch/repl`)

Replica: fake `_pin_repo_root` markers (`pyproject.toml`,
`src/rumpun/report.py`, `.venv/bin/python` symlink to the repo venv),
fake `.rumpun/akar` (two records), `tools/coldstart_check.py` = w1's
workspace copy, sha256 `b8517210…` at copy time, and the 182-item tests
file. Repo file sha at baseline: `2b95398f…` (unchanged since s37 landed).

| proof | result | evidence |
|---|---|---|
| four pins vs w1's checker | 4 passed, 5.81s, exit 0 | `repl-pins-green.txt` |
| manual sabotage of w1's checker | exit 1, `STEP 8 FAIL: rumpun evolve plan .rumpun/musim/s1.yaml (rc=1)`, wall 1.25s | `sabotage-demo.txt` |
| headless 11-step rehearsal (no checker, CLI only) | LOOP OK, s2 artifacts in place | `probe.txt` |

The pins exercise real subprocess runs: each checker run spawns six to
eleven `python -m rumpun` CLI subprocesses (visible in the logged
`run: (cd … && …)` lines in `red-pins.txt`), and the sabotage demo shows
the stub failing exactly the evolve step at 1.25s wall.

## Rehearsal intel (probe, for the record)

- `rumpun evolve plan` drafts from the CURRENT parent file: the drafted
  s2 arrives already stub-routed (the checker's step-2 edit carries over).
- Lint requires the four `primary_change` fields (baseline, expected_band,
  rollback, eval_window) on a parented season — the drafted skeleton ships
  them empty, so w1's step 9 fill is load-bearing. w1 also adds an
  `akar:audit-1@<digest>` evidence citation; the headless rehearsal passed
  with the four fills alone.
- A sitecustomize stub on PYTHONPATH reaches every `python -m rumpun`
  subprocess of the checker run (mechanism probe in `probe.txt`).

## Merge notes for the harness

- Merge w1's `tools/coldstart_check.py` and this tests file together: the
  pins fail (never skip) while the extension is absent from main, and all
  four go green on w1's copy as proven.
- Pin 1 pins the summary at exactly 11 steps; w1 derives the count from
  the steps list, so a step-count change on either side surfaces here.
- Pin 4 scope: the whole repo `.rumpun` (21,896 files, ~3.6s warm per
  pass) minus volatile dirs — the live season's lanes (`.rumpun/rimba/s38/**`),
  the harness state dir (`.rumpun/.omc/`), and `__pycache__`. At merge
  time (s38 closed) the live-lane exclusion covers the season being
  harvested; if the suite runs while a LATER season is live, its lane
  writes are outside the excluded prefix and could trip the byte-compare —
  run the suite without a concurrent agent season.
- Pin 3 is uid-independent (unlike s37's read-only-target sabotage, which
  needs uid != 0); the PYTHONPATH stub works under any user.
- `pytest -k` does not filter in this environment (venv pytest 9.1.1);
  select the pins by explicit node ID.

## Environment note

- Ruff under `.rumpun/rimba/` checks zero files without
  `--no-respect-gitignore`; every ruff run here used the flag.
