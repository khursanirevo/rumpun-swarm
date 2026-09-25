# rumpun

rumpun is a CLI that bootstraps a self-evolving multi-agent swarm in a folder.
The swarm is declared in YAML: one season file names the pipeline, the agents,
and the stop rules. Git history over `.rumpun/` is the evolution ledger; each
season closes with a harvest verdict that becomes cited evidence for the next
season's plan.

## Install

Requires Python 3.10 or newer. From a clone of this repository, at the repo
root:

```
uv pip install -e .
```

This installs the `rumpun` command.

## Quickstart

Run inside the folder that will hold the project. Commands are listed in
order; each depends on the one above it.

```
rumpun init
```

Scaffolds `.rumpun/` in the target folder (default: the current one):
`rumpun.yaml`, `musim/s1.yaml` (the seed season), `musim/_template.yaml`,
`prompts/base/`, `akar/`, and `rimba/`.

```
rumpun models --write
```

Detects which model routes this machine can spawn and fills `routes:` in
`.rumpun/rumpun.yaml`. `--probe` also sends one small completion per claude
route and spends quota.

Edit two files before the next step; lint blocks on empty fields:

- `.rumpun/rumpun.yaml` — fill `campaign.goal` and `campaign.metric`.
- `.rumpun/musim/s1.yaml` — fill `goal` and `metric`; set each benih `route:`
  to a key from the `routes:` block written above (`glm`, `claude`,
  `gpt-5.6-sol`, ...). The seeded `glm-5.2`/`fable` values are placeholders.

```
rumpun lint .rumpun/musim/s1.yaml
```

Validates the season: structure, DAG shape, artifact contracts, prompt paths,
evidence citations. Errors block `season start`.

```
rumpun graph .rumpun/musim/s1.yaml
```

Prints the season pipeline as a mermaid DAG.

```
rumpun direct "one line of operator intent"
```

Appends a pending directive to the akar ledger; `rumpun direct --list`
shows them. Directives are consumed at the next phase boundary, never
injected into a running agent.

```
rumpun season start .rumpun/musim/s1.yaml
```

Spawns the benih agents as one-shot child processes and blocks until a stop
rule fires. Run `rumpun season stop s1` from another terminal to stop early.

```
rumpun board s1
```

Prints the season snapshot: status, duration, per-agent state. Same view as
`rumpun season status s1`; both take `--json`.

```
rumpun season show s1
```

Prints the season detail: status line, each agent's deliverable files, and
lane event counts. `--json` prints the machine form.

```
rumpun season list
```

Prints one line per season: id, status, duration, agent count. Seasons whose
state is absent (never started, or run manually before the engine existed)
print `no state`.

```
rumpun season report s1
```

Writes the static HTML report to `.rumpun/rimba/s1/report.html`.

```
rumpun season report s1 --serve
```

Renders the report first, then serves `.rumpun/rimba/` read-only on
http://localhost:8611 (open `s1/report.html`); Ctrl-C stops the server and
exits 0.

```
rumpun harvest s1 --verdict WIN --implies "seed pipeline ran end to end"
```

Closes the season: appends one record with the verdict and the implies line
to the akar ledger.

```
rumpun evolve plan .rumpun/musim/s1.yaml
```

Drafts `.rumpun/musim/s2.yaml` from the latest season with an empty
`primary_change` skeleton. Fill `baseline`, `expected_band`, `rollback`, and
`eval_window`, and add akar citations under `evidence:`.

```
rumpun evolve apply .rumpun/musim/s2.yaml
```

Runs the lint gate on the draft; apply fails while skeleton fields are empty.

## Not implemented yet

These verbs parse but print a not-implemented notice and exit 2:

| Command | Purpose |
|---|---|
| `rumpun evolve approve` | approve a drafted evolution (panel stage) |
| `rumpun evolve reject` | reject a drafted evolution; runs the `on_reject` policy |
| `rumpun evolve rollback` | rollback to the last good season |

## The `.rumpun/` directory

Everything except `rimba/` is committed; git history over it is the evolution
ledger. Relative paths in season YAML resolve against `.rumpun/`.

| Path | Holds | Tracked |
|---|---|---|
| `rumpun.yaml` | campaign config: goal, metric, autonomy stage, budget cap, model routes | yes |
| `musim/` | one YAML per season; `_template.yaml` shows the non-seed shape | yes |
| `prompts/` | phase prompt templates: `base/` defaults, `prompts/sN/` season overrides | yes |
| `akar/` | append-only evidence ledger: harvest records and findings | yes |
| `rimba/` | per-season workspaces: prompts, logs, exit files, reports | no (gitignored) |

## Season lifecycle

In fight mode every benih works alone in its own workspace and sees no other
agent's output until harvest. In collab mode each benih also appends rows to
a shared lane file and re-reads it every iteration; lane rows are leads to
check, not facts.

A season ends when all agents exit, one stalls past `stall_minutes`, the
benih budget runs out, or the operator stops it.

## Design

DESIGN.md at the repo root is the canonical design record: decisions,
proposals, verdicts, and the build order. Season YAML cites akar records
(`akar:<record-id>@<sha>`) as evidence for methodology changes; lint refuses
to start a season whose citations do not resolve.
