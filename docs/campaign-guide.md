# Campaign guide — from zero to a sealed first season

The README's verbs table documents every command. This guide walks the path
behind that table: a fresh folder to a sealed, checked, pushed first season,
and the loop that keeps a campaign going after it. Every command is named
exactly as the parser accepts it. The pin
`tests/test_s121_campaign_guide.py` fails the suite when a command here
drifts from the parser.

The campaign's own history is the worked example. Its close protocol lives
in `.rumpun/RESUME.md` under "Season-close protocol"; this guide is the
operator-facing version of the same path.

## 1. Point rumpun at your repo

Run inside the folder that holds your project:

```shell
rumpun init
```

`rumpun init` writes `.rumpun/` beside your code and refuses an existing
campaign. What lands:

| Path | Holds |
|---|---|
| `.rumpun/rumpun.yaml` | campaign config: goal, metric, autonomy stage, budget cap, `schema: 1`, routes |
| `.rumpun/CHANGELOG.md` | schema history; an unknown schema version refuses mutating verbs |
| `.rumpun/seasons/s1.yaml` | the seed season, with FILL markers |
| `.rumpun/seasons/_template.yaml` | the non-seed shape: the `primary_change` block |
| `.rumpun/seasons/_competition.yaml` | the competition-season shape |
| `.rumpun/seasons/_steady-state.yaml` | the steady-state shape: the light lanes and the operator's decision gate |
| `.rumpun/prompts/base/` | seven prompt templates: execute, evaluate, plan, hypothesize, falsify, analyze, rank_gaps |
| `.rumpun/ledger/` | the append-only evidence ledger |
| `.rumpun/runs/` | live season state, gitignored |
| `.rumpun/README.md` | the scaffold's own card |
| `.rumpun/adhd-rules.md` | the i-have-adhd output-rules card |
| `tools/artifact_check.py` | the independent checker `rumpun check` runs |

Everything under `.rumpun/` except `runs/` is git-tracked. Git history over
it is the evolution ledger.

Detect the model routes this machine can spawn and fill the `routes:` block
in `.rumpun/rumpun.yaml`:

```shell
rumpun models --write
```

Without flags the verb is read-only. `--probe` sends one small completion
per claude route and spends quota. The scaffolded writer route keys
(`glm-5.2`, `fable`) stay placeholders until the routes block names real
keys. The `glm` route serves `glm-5.3` (probe-checked 2026-09-20).

On a campaign whose `routes:` block already names real keys, `--write`
re-detects and diffs the detected routes against the block. It writes
only the newly detected keys, after the last existing entry. The log
names them (`+ claude, newkid`). Existing lines stay byte-untouched:
hand-tuned commands and comments survive every run. A second run finds
no new keys and writes nothing. No `routes:` block at all is a refusal
that leaves the file untouched.

Edit two files before the first lint:

- `.rumpun/rumpun.yaml`: fill `campaign.goal` and `campaign.metric`. Set
  `budget.campaign_cost_cap` to a number. The tool flags an unset cap; the
  operator sets it.
- `.rumpun/seasons/s1.yaml`: fill `goal` and `metric`. Set each writer's
  `route:` to a key from the `routes:` block.

The competition shape: the scaffold also emits
`.rumpun/seasons/_competition.yaml`, the competition-season shape
(baseline -> validate -> submit -> improve). Copy it to
`seasons/s<N>.yaml` and fill every FILL field before the first lint:
`id`, `parent`, `goal`, `metric`, `methodology.approach`, the
`methodology.evidence` citations, `primary_change.expected_band`,
`primary_change.rollback`, the submit node's `prompt`, and each writer's
`name`. Set each writer's `route:` to a key from the `routes:` block and
`budget.minutes` to a positive int. A wiped copy refuses at the gate
naming each empty field; a filled copy lints clean before
`season start`.

Preview the pipeline, then pass the gate:

```shell
rumpun graph .rumpun/seasons/s1.yaml
rumpun lint .rumpun/seasons/s1.yaml
```

Lint checks structure, the DAG shape, artifact contracts (a phase that
reads an artifact needs a phase that writes it), prompt paths, and evidence
citations. Exit 1 means errors, and errors block `season start`. The common
first-run errors: an empty goal or metric, a route key missing from
`routes:`, a prompt path that does not exist. The seed carries no evidence
citations and `parent: null` waives the `primary_change` block.

## 2. Run the first season

```shell
rumpun season start .rumpun/seasons/s1.yaml
```

The start runs the lint preflight, spawns one process per writer, and
blocks until a stop rule fires. The seeded stop rules: all writers exited,
a stall past `stall_minutes`, or the season budget exhausted. Each writer
works alone in its own workspace under `.rumpun/runs/s1/`.

From another terminal while the season runs:

```shell
rumpun season status s1
rumpun season stop s1
```

Exit codes: `completed`, `stopped_operator`, and `running` exit 0. `failed`,
`stopped_stall`, and `stopped_budget` exit 1. `rumpun season list` prints
one line per season. `rumpun season show s1` names each writer's
deliverable files. `rumpun season report s1` writes a static HTML report
under `.rumpun/runs/s1/`.

The notes gate: demand `notes.md` in every writer prompt. A writer that
exits rc 0 without shipping its notes.md is machine-marked incomplete, the
mark lands on its state snapshot and its results row, and the harvest
record carries the line.

## 3. Close the season

A close is five moves: the design row, the design lint, the harvest, the
independent check, the push.

The campaign keeps `DESIGN.md` at the repo root with one row per season:

```text
| season | verdict | ships (one line) |
|---|---|---|
| s1 | WIN | src/example.py: the first step; tests/test_example.py: 3 pins |
```

The ships cell names the surfaces the season shipped. Gate the row before
closing:

```shell
rumpun lint DESIGN.md
```

This is the design lint: every surface a ships row names must exist in the
tree. Name real tracked paths in full (`src/...`), never bare basenames.

Harvest the season:

```shell
rumpun harvest s1 --verdict WIN \
  --implies "the seed pipeline ran end to end" \
  --band "WIN if the pipeline completes, LOSS if any writer ships nothing" \
  --observed "completed in 22 minutes, 2 writers, 0 stall"
```

`--verdict` takes WIN, LOSS, NEUTRAL, INVALID. `--band` carries the
expected band for the season metric and `--observed` the measured result;
both are recorded verbatim. A second harvest of the same season is refused.

Seal the standing usefulness assessment beside the harvest, so every close
proves the campaign is still worth running:

```shell
rumpun harvest s1 --verdict WIN \
  --implies "the seed pipeline ran end to end" \
  --assessment-file assessment-s1.yaml
```

The assessment file (quoted values, so ` #` tokens never start a YAML
comment):

```yaml
verdict: "CONTINUE"
basis: "why the campaign continues, citing ledger records"
fronts:
- name: "the one open front"
  owner: "campaign"
  basis: "what is open, with the record id that names it"
  next: "the next action"
satisfied:
- "what landed since the last seal, with record ids"
```

Fields: `verdict` is CONTINUE, PAUSE, or EXHAUSTED. The inputs pre-flight
before any close write; a bad file refuses the close. The campaign's
planner announces the assessment cadence each close; a fresh campaign
should seal one every close while the work is worth continuing.

### The lane-commit rule

During a season a writer may commit exactly its bounded files: the files
its brief bounds, nothing else. The subject stays <= 50 chars and
season-tagged (`feat: s123 fixes the gate`). The close worker folds the
rest: the close commit names its paths (the pathspec form), so a
concurrent session's staged work cannot ride it.

Commit the close, then run the independent check at the new HEAD:

```shell
git add <new-files>
git commit -m "feat: s1 closes the seed season" -- <paths>
rumpun check s1 HEAD
```

The checker rebuilds the closed season's deliverables from the close
commit in a clean extract and appends the `check-s1` ledger record.
VERIFIED releases the next start. A close whose commit carries no pins lane
(`tests/test_<sid>_*.py`) and whose ships row claims no pins takes the named
skip instead: exit 0, no record. A DELTA gates the next start until a
fixed rerun lands (as `check-s1-2`) or the operator releases it:

```shell
rumpun waive s1 --reason "why the operator releases this start"
```

Then push. The campaign pushes main to origin at each close; rumpun itself
never runs git:

```shell
git push
```

A FAILED or INVALID season takes no post-commit check: no deliverables, no
record, no block.

## 4. Keep going

Reflect, then seed the next season:

```shell
rumpun audit --last 10
rumpun evolve plan .rumpun/seasons/s1.yaml
```

`audit` appends one evidence-cited candidates record (at most 3 candidates
per record) and prints the candidates. `evolve plan` drafts `s2.yaml` from
the parent. Fill the draft:

- the `primary_change` block: type, node, baseline, expected_band,
  rollback, eval_window
- `evidence:` citations in the `ledger:<record-id>@<sha>` form

Then pass the draft through the gate and record the approval:

```shell
rumpun evolve apply .rumpun/seasons/s2.yaml
rumpun evolve approve .rumpun/seasons/s2.yaml
```

Nothing auto-applies: `evolve apply` is the lint gate and `evolve approve`
records the operator approval. `evolve reject` moves a draft to
`seasons/rejected/` and records the containment policy. `evolve rollback`
contains an applied season. Every path argument must sit inside the
campaign: resolution walks up to the nearest `.rumpun/`.

The loop is the campaign's event consumer:

```shell
rumpun loop --once
```

It drains the event bus under `.rumpun/events/`, dispatching each season
event once. For a finished season it runs close-prep: the planner-drafted
next-season yaml lands under `.rumpun/runs/<sid>/seasons/`. Without
`--once` the loop blocks on new events; `--exec CMD` runs a command per
event with the event JSON on stdin and `RUMPUN_EVENT` set.

The board mirrors the ledger on demand:

```shell
rumpun board --dry-run --sync s1
rumpun board --sync s1
```

`--sync` comments the sealed harvest record onto the season's board issue
and closes it. `--dry-run` prints without writing. This needs the GitHub
board wired to the repo; skip the sync until one exists.

Re-entry after any break:

```shell
rumpun resume
rumpun kanban
rumpun direct --list
```

`resume` prints the one-screen re-entry: newest close, running seasons,
pending items, audit. `kanban` prints the four-column campaign board.
`direct` appends an operator directive to the ledger (`rumpun direct "one
line of operator intent"`); `--list` prints them, pending first.

Plugins are optional. A pack is a directory with a manifest and `priors/`;
install, publish, and pull digest-verify the tree. A first season needs no
plugin; when a season cites pack priors, the digest must verify.

```shell
rumpun plugin install /path/to/pack
rumpun plugin list
```

### The steady state

After a close, with no approved next season, the campaign idles in a
steady state: light lanes keep the machinery warm while the operator
decides what runs next. A light lane re-proves an existing surface and
stops there. The standing three:

- the lint sweep: the guide lint, the pins, and `ruff check` on the
  touched files
- the route probes: one bounded writer call per route, verdict recorded
  in the lane notes
- the rehearsals: a documented flow re-run end to end, drift fixed

The shape: `rumpun init` emits `.rumpun/seasons/_steady-state.yaml`, the
steady-state season shape. The three standing lanes sit in the pipeline
(lint-sweep, route-probes, rehearsals) and the operator's decision gate
sits in the band. Copy it to `seasons/s<N>.yaml` and fill every FILL
field before the first lint; the filled shape lints clean, and a
wiped-fill copy refuses naming its errors.

A light lane invents no work. Anything heavier - a new season, a
methodology change, spend - waits behind the operator's decision gate.
The reads that feed the decision:

```shell
rumpun audit --last 10
rumpun kanban
rumpun resume
```

The operator's word lands in the ledger:

```shell
rumpun direct "the steady state holds until I say otherwise"
```

Leave the steady state on a fresh candidate class the audit surfaces and
the operator approves, or on the operator's word alone. Leaving means a
new season: `evolve plan`, the `evolve apply` gate, `evolve approve`
(the block at the top of this section).
## The rules the loop enforces

- Every methodology change cites ledger evidence; lint refuses to start a
  season whose citations do not resolve.
- Nothing auto-applies. At the `manual` autonomy stage the operator
  approves through `evolve apply` and `evolve approve`.
- The budget cap: the tool flags an unset cap; the operator sets it.
- Every close: the design row, the design lint, the harvest, the
  assessment, the check, the push.
