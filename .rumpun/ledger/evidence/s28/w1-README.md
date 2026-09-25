# rumpun

rumpun is a CLI that bootstraps a self-evolving multi-agent swarm in a folder.
The swarm is declared in YAML: one season file names the pipeline, the agents,
and the stop rules. Git history over `.rumpun/` is the evolution ledger; each
season closes with a harvest verdict that becomes cited evidence for the next
season's plan. Engine code stays fixed during a campaign; only YAML evolves.

## Install

Requires Python 3.10 or newer and `pyyaml`. From a clone of this repository,
at the repo root:

```
uv pip install -e .
```

This installs the `rumpun` command.

## Quickstart

Run inside the folder that will hold the project. Steps in order; each depends
on the one above it.

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
`.rumpun/rumpun.yaml`. Read-only without flags. `--probe` sends one small
completion per claude route and spends quota.

Edit these before the next step; lint blocks while the season fields are empty:

- `.rumpun/rumpun.yaml` — fill `campaign.goal` and `campaign.metric`. Set
  `budget.campaign_cost_cap` before starting; the tool flags, the operator sets.
- `.rumpun/musim/s1.yaml` — fill `goal` and `metric`; set each benih `route:`
  to a key from the `routes:` block written above. The seeded `glm-5.2`/`fable`
  values are placeholders.

```
rumpun lint .rumpun/musim/s1.yaml
```

Validates the season: structure, DAG shape, artifact contracts, prompt paths,
evidence citations. Exits 1 on errors, and errors block `season start`.

```
rumpun graph .rumpun/musim/s1.yaml
```

Prints the season pipeline as a mermaid DAG.

```
rumpun direct "one line of operator intent"
```

Appends a pending directive to the akar ledger; `rumpun direct --list` prints
them, pending first.

```
rumpun season start .rumpun/musim/s1.yaml
```

Runs the lint preflight, spawns the benih agents as one-shot child processes,
and blocks until a stop rule fires. `rumpun season stop s1` from another
terminal stops the season early.

```
rumpun harvest s1 --verdict WIN --implies "seed pipeline ran end to end"
```

Closes the season: appends one record with the verdict and the implies line to
the akar ledger. `--band` and `--observed` carry the expected band and the
measured result into the verdict row.

```
rumpun audit --last 10
```

Reflects over the last N seasons (default 10), appends the evidence-cited
candidate-mutation record to akar, and prints the candidates.

The evolution verbs then turn the closed season into the next one; see
"The self-evolution loop" below.

## Verbs

Every verb below exists in `rumpun --help` at 0.11.0.

| Verb | What it does | Caveat |
|---|---|---|
| `init [TARGET]` | scaffolds `.rumpun/` in TARGET (default: cwd) | |
| `models [--write] [--probe]` | detects spawnable model routes; `--write` fills `rumpun.yaml` routes | `--probe` spends quota: one completion per claude route |
| `lint FILE` | validates a season YAML: structure, DAG, contracts, prompt paths, citations | errors block `season start` |
| `graph FILE` | prints the season pipeline as a mermaid DAG | shows the declaration, not runtime state |
| `direct [TEXT] [--list]` | appends or lists operator directives in the akar ledger | append-only: nothing is injected into a running agent |
| `board ID` | prints the season snapshot: status, duration, per-agent state | same view as `season status`; only `season status` takes `--json` |
| `harvest ID --verdict --implies [--band] [--observed]` | closes the season into akar: verdict WIN/LOSS/NEUTRAL/INVALID plus implies line | a second harvest of the same season is refused; band and observed are recorded verbatim |
| `audit [--last N]` | reads the season ledger, appends one evidence-cited candidate record, prints candidates | appends a record on every run, also with zero candidates; a record carries at most 3 candidates |
| `season start FILE [--json]` | lint preflight, spawn the benih, block until a stop rule fires | exits 1 when the season failed, stalled, or hit its budget |
| `season stop ID` | stops the season from another terminal | exit code follows the same status mapping |
| `season status ID [--json]` | prints the snapshot from persisted state | exit code reflects the season status |
| `season list` | one line per season: id, status, duration, agent count | seasons without persisted state print `no state` |
| `season show ID [--json]` | status line, each agent's deliverable files, lane event counts | deliverables exclude engine bookkeeping files |
| `season report ID [--serve]` | writes the static HTML report to `.rumpun/rimba/sN/report.html` | renders from persisted state: a running season's report is a snapshot at render time; `--serve` then serves `.rumpun/rimba/` read-only on http://localhost:8611 until Ctrl-C (exit 0) |
| `evolve plan FILE` | drafts `sN+1.yaml` from the parent season | ships with an empty `primary_change` skeleton; apply fails until it is filled |
| `evolve apply FILE` | runs the lint gate on the draft | nothing auto-applies; this gate is the only path to a lint-clean draft |
| `evolve approve FILE` | records the operator approval in akar | the draft file itself is not modified |
| `evolve reject FILE` | moves the draft to `musim/rejected/` | records the on_reject policy: rollback to last good, pause, escalate after 2 consecutive rejects |
| `evolve rollback ID` | contains an applied season: its YAML moves to `musim/rejected/` | never runs git; a code-level restore is an explicit git revert by the operator |

## The self-evolution loop

One cycle: season -> harvest -> audit -> seed the next season.

1. The season runs under its declared pipeline and stop rules.
2. `rumpun harvest` closes it with a verdict and an implies line.
3. `rumpun audit` reads the ledger (last 10 seasons by default) and appends
   one record with per-check findings: phase liveness against each phase's own
   declared artifact, stall recurrence, verdict histogram, per-route outcomes,
   band calibration, and the budget-cap flag.
4. `rumpun evolve plan` drafts the next season from the parent; the operator
   fills `primary_change`, cites evidence, and passes `evolve apply`.

Rules the loop enforces on itself:

- Every methodology change cites akar evidence (`akar:<record-id>@<sha>`);
  lint refuses to start a season whose citations do not resolve.
- A record carries at most 3 candidates; the budget-cap finding never proposes
  a mutation, it names the unset cap and waits for the operator.
- Nothing auto-applies. At the `manual` autonomy stage the operator approves
  through `evolve apply`/`approve`; a reject or rollback records the
  containment policy in akar.

### The corpus gate

`tools/replay_corpus.py` is the cross-season regression gate. It discovers the
archived scripts under `.rumpun/akar/evidence/`, runs the six-script repro
corpus against the current `src/` with per-script isolation, and writes a
markdown matrix (`replay-matrix.md`). Every script gets an honest verdict:
PASS, FAIL, DRIFT, or SKIP with a reason; an unmatched script still emits a
row marked UNCLASSIFIED. `rumpun audit` reads the newest matrix since s26: a
FAIL or REGRESSION row arms a candidate placed first, citing the script and
its first failing line; an all-green matrix becomes a plain finding.

### The dashboard

`tools/render_dashboard.py` is the maintained render loop: it renders the
campaign index, the discoveries pages, and every season that has persisted
state; seasons without state are skipped with a logged reason. Renders are
deterministic: no JavaScript, no external assets, byte-identical re-runs.
`rumpun season report --serve` serves the same tree read-only on
http://localhost:8611.

## The `.rumpun/` directory

Everything except `rimba/` is committed; git history over it is the evolution
ledger. Relative paths in season YAML resolve against `.rumpun/`.

| Path | Holds | Tracked |
|---|---|---|
| `rumpun.yaml` | campaign config: goal, metric, autonomy stage, budget cap, model routes | yes |
| `musim/` | one YAML per season; `_template.yaml` shows the non-seed shape | yes |
| `prompts/` | phase prompt templates: `base/` defaults, `prompts/sN/` season overrides | yes |
| `akar/` | append-only evidence ledger: harvest, audit, approval, and rollback records | yes |
| `rimba/` | per-season workspaces: prompts, logs, exit files, reports | no (gitignored) |

## Season lifecycle

The seeded pipeline is two phases: execute (the benih build the step) and
evaluate (the judge writes verdicts). Extra phases can be declared per-season
when a task needs them.

In fight mode every benih works alone in its own workspace and sees no other
agent's output until harvest. In collab mode each benih also appends rows to a
shared lane file and re-reads it every iteration; lane events refine, they
never gate, and lane rows are leads to check, not facts.

A season ends when all agents exit, one stalls past `stall_minutes`, the benih
budget runs out, or the operator stops it. Stall progress is appended log
bytes: touching the log without appending provides no progress, and a caller
with no byte history keeps the mtime estimate. `completed`, `stopped_operator`,
and `running` exit 0; `failed`, `stopped_stall`, and `stopped_budget` exit 1.

## Design

DESIGN.md at the repo root is the canonical design record: decisions,
proposals, verdicts, and the build order. Report pages carry provenance labels
([H] harness-observed, [A] agent-authored, [D] derived) on displayed values.

## Version

0.11.0. `pyproject.toml`, `src/rumpun/__init__.py`, and `rumpun --version`
agree.
