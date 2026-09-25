# notes — w3 README

What I checked so every README command is real (source-read, not guessed):

- `src/rumpun/scaffold.py` — init seeds `.rumpun/musim/s1.yaml` itself
  (plus `_template.yaml`, `prompts/base/*.md`, `akar/.gitkeep`,
  `rimba/.gitignore`), so the quickstart edits s1 instead of creating it;
  init refuses to overwrite an existing `rumpun.yaml`.
- `src/rumpun/cli.py` — verb surface cross-checked against the task list:
  implemented verbs match exactly; `season list/show/direct` and
  `evolve approve/reject/rollback` are argparse stubs whose handlers return
  2. `board ID` dispatches to the same handler as `season status ID`.
- Live check: `.venv/bin/rumpun --help`, `season --help`, `evolve --help`,
  `harvest --help` — printed surface matches the README verbatim.
- `src/rumpun/lint.py` — empty `goal`/`metric` is an error, so the edit step
  precedes `lint`; a non-seed season needs `primary_change` with `baseline`,
  `expected_band`, `rollback`, `eval_window` all filled, so `evolve apply`
  comes after the fill step.
- `src/rumpun/engine.py` — `season start` raises EngineError when `routes:`
  is empty or a benih route is not a routes key; four terminal states:
  completed / stopped_stall / stopped_budget / stopped_operator (the four
  stop rules in the lifecycle section); `start` blocks while watching, so
  the README tells the operator about the second-terminal `season stop`.
- `src/rumpun/routes.py` — `models --write` patches only the literal
  `routes: {}` scaffold line; keys are family labels (`glm`, `claude`,
  `gpt-5.6-sol`, ...), which is why the quickstart says to edit the seeded
  placeholder routes (`glm-5.2`, `fable`); `--probe` runs one completion per
  claude route and spends quota, so the README marks it opt-in.
- `src/rumpun/evolve.py` — `plan` requires the parent to be the latest
  season and drafts `musim/s<N+1>.yaml` with an empty skeleton; `apply` is a
  lint gate that blocks on empty skeleton fields.
- `src/rumpun/harvest.py`, `src/rumpun/report.py` — harvest appends one akar
  record per close and needs engine state to exist (so it runs after
  `season start`); report writes `.rumpun/rimba/<id>/report.html`.
- `.rumpun/README.md` and the scaffolded README inside `scaffold.py` — the
  quickstart mirrors their "First season" list, reordered so
  `models --write` precedes the benih-route edit.
- Version strings disagree: `pyproject.toml` says 0.2.0,
  `src/rumpun/__init__.py` says 0.1.0, `cli.py`'s docstring and the
  installed CLI say v0.3.0. The README states no version number;
  integration should reconcile the three before release.
- No git remote is configured, so Install says "from a clone" without a URL.

Not done, and why: no end-to-end quickstart run in a scratch folder — the
task allows writing only README.md and notes.md in this workspace, and
`season start` would spawn real model routes (quota). Commands are grounded
in the code paths and the live `--help` output above instead.
⚠️ expected-projected, not executed.
