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

The campaign guide walks the same path in full: [docs/campaign-guide.md](docs/campaign-guide.md).

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

Every verb below exists in `rumpun --help`.

| Verb | What it does | Caveat |
|---|---|---|
| `init [TARGET] [--plugin PACKDIR]` | scaffolds `.rumpun/` in TARGET (default: cwd); `--plugin PACKDIR` installs a pack and scaffolds pack-first (repeatable) | |
| `models [--write] [--probe]` | detects spawnable model routes; `--write` fills `rumpun.yaml` routes | `--probe` spends quota: one completion per claude route |
| `lint FILE` | validates a season YAML: structure, DAG, contracts, prompt paths, citations | errors block `season start` |
| `graph FILE` | prints the season pipeline as a mermaid DAG | shows the declaration, not runtime state |
| `direct [TEXT] [--list]` | appends or lists operator directives in the akar ledger | append-only: nothing is injected into a running agent |
| `board [ID] [--sync SID] [--dry-run] [--map SID URL] [--mirror]` | prints the season snapshot; `--sync SID` comments the season's board issue with its sealed harvest record and closes it; `--map SID URL` records lane-to-issue answers in `.rumpun/board-map.json`, read first by `--sync`; `--mirror` mirrors the ledger verdicts onto the board cards (create missing, update drifted, idempotent) | same view as `season status`; only `season status` takes `--json`; `--sync` and `--mirror` have `--dry-run` |
| `harvest ID --verdict --implies [--band] [--observed] [--assessment-file] [--strict]` | closes the season into akar: verdict WIN/LOSS/NEUTRAL/INVALID plus implies line; `--assessment-file` seals the standing usefulness assessment `usefulness-<sid>` beside the harvest; `--strict` passes the close check's verdict exit through | a second harvest of the same season is refused; band and observed are recorded verbatim; the assessment inputs pre-flight before any close write |
| `audit [--last N] [--corpus] [--panel SID] [--dry-run] [--panel-sweep] [--outcome-file PATH]` | reads the season ledger, appends one evidence-cited candidate record, prints candidates; the `--last` listing names each season's judge verdict, its latest panel verdict, and the dissent flag; `--corpus` refreshes the replay matrix first; `--panel SID` seals a second-opinion request marked pending; `--dry-run` prints the `--panel` review writing nothing; `--panel-sweep` lists the pending panel records, and with `--outcome-file` seals each named outcome as `<id>-verdict` or `<id>-error` | appends a record on every run, both with zero candidates; a record carries at most 3 candidates; `--panel` spends route credits |
| `season start FILE [--json]` | lint preflight, spawn the benih, block until a stop rule fires | exits 1 when the season failed, stalled, or hit its budget |
| `season stop ID` | stops the season from another terminal | exit code follows the same status mapping |
| `season status ID [--json]` | prints the snapshot from persisted state | exit code reflects the season status |
| `season list` | one line per season, newest first: id, status, duration, agent count | seasons without persisted state print `no state` |
| `season show ID [--json]` | status line, each agent's deliverable files, lane event counts | deliverables exclude engine bookkeeping files |
| `season report ID [--serve]` | writes the static HTML report to `.rumpun/rimba/sN/report.html` | renders from persisted state: a running season's report is a snapshot at render time; `--serve` then serves `.rumpun/rimba/` read-only on http://localhost:8611 until Ctrl-C (exit 0) |
| `evolve plan FILE` | drafts `sN+1.yaml` from the parent season | ships with an empty `primary_change` skeleton; apply fails until it is filled |
| `evolve apply FILE` | runs the lint gate on the draft | nothing auto-applies; this gate is the only path to a lint-clean draft |
| `evolve approve FILE` | records the operator approval in akar | the draft file itself is not modified |
| `evolve reject FILE` | moves the draft to `musim/rejected/` | records the on_reject policy: rollback to last good, pause, escalate after 2 consecutive rejects |
| `evolve rollback ID` | contains an applied season: its YAML moves to `musim/rejected/` | never runs git; a code-level restore is an explicit git revert by the operator |
| `epics [--init]` | prints the epic rollup from `.rumpun/epics.yaml`: id, season span, verdict rollup, title; `--init` scaffolds the yaml from the season files; members name their harvest basis, latest panel verdict, and any dissent | `--init` never overwrites; the rollup renders the dissent-adjusted counts beside the raw totals |
| `check SID COMMIT [--out-dir DIR]` | runs the independent artifact check of a closed season from its close commit; appends the `check-<sid>` record; `--out-dir DIR` writes the record into DIR instead of the live ledger | a DELTA gates the next start until a VERIFIED rerun or `rumpun waive` |
| `waive SID --reason` | appends the `waiver-<sid>` record releasing a containment-blocked season start | the reason is recorded verbatim |
| `kanban` | prints the campaign board: backlog, doing, need-human, done; NEED HUMAN cards carry the four-sentence shape | renders from existing state, writes nothing |
| `plugin install PACKDIR, list, distill PACK_NAME --source SOURCE, publish NAME --remote REMOTE, pull NAME --remote REMOTE` | pack tools: digest-verified install, the installed list, the distill export of proven gates into a draft pack, publish and pull over a git remote; `--source` is recorded verbatim as the manifest source; `--remote` names the git remote for publish and pull | install, publish, and pull digest-verify the tree |
| `resume` | prints the one-screen re-entry: newest close, running seasons, pending items, audit | |
| `loop [--exec CMD] [--once]` | event-driven campaign consumer: dispatch on season events; `--exec` runs a command per event with the event JSON on stdin and `RUMPUN_EVENT` set; `--once` drains the backlog then exits | |
| `statusline [--home] [--install] [--uninstall]` | prints the one-line campaign segment (running season, lane states, last verdicts) for shell statusbars; `--install` composes the Claude Code statusLine to run the original command plus this segment, `--uninstall` restores | |
| `ledger correct ID --reason` | appends a sealed correction record for a flawed ledger record | the flawed record never rewrites |

Every flag the parser accepts is named in its row or intentionally hidden:
the per-verb `--help`/`-h` pair and the global `rumpun --version`. A parser
flag named in neither its row nor this line is drift and fails the reverse
flag audit.

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

## The second opinion

`rumpun audit --panel sN` composes the audit panel's review input for a season and
seals a `panel-<sid>` ledger record marked pending. A second run derives the next
free id in the family (`panel-s69`, then `-2`, then `-3`); the first record never
rewrites. `rumpun audit --panel-sweep` lists the pending records; with
`--outcome-file` it seals each named outcome as `<id>-verdict` or `<id>-error`
from an explicit yaml, the request records never rewritten. The `audit --last`
listing names each season's judge verdict beside its latest panel verdict, with
the `dissent:<panel verdict>` flag when the two diverge.

## Epics

`rumpun epics` renders the epic rollup from `.rumpun/epics.yaml`; `rumpun epics
--init` scaffolds the yaml from the season files and never overwrites. Each member
line names its harvest basis (`<sid>-harvest@<sha8>` for a WIN or LOSS, the
declared basis verbatim for anything else), the latest panel verdict record beside
its basis, and `dissent:<panel verdict>` when the panel diverges from the judge.
The rollup prints the dissent-adjusted counts beside the raw WIN totals.

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

A writer that exits rc 0 without shipping its notes.md gains the additive
incomplete marker on its state snap and its results row. The harvest record
carries the incomplete line, and the deterministic season report renders the
mark.

The lane-commit rule: during a season a writer commits exactly its bounded
files, subject <= 50 chars, season-tagged. The close worker folds the rest.

## Design

DESIGN.md at the repo root is the canonical design record: decisions,
proposals, verdicts, and the build order. Report pages carry provenance labels
([H] harness-observed, [A] agent-authored, [D] derived) on displayed values.

## Version

The package version lives in `pyproject.toml` and moves at every close: MINOR per
feature close, PATCH per fixes. The newest dated section in CHANGELOG.md names it;
tests/test_s118_docs_truth.py fails the suite while the two diverge.
