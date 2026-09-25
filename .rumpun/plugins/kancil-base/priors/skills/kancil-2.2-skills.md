---
kancil-version: 2.2.5
source-commit: 7700a1b958ea89fd737dbecb25c9aa74a1bcaed2
---

# kancil 2.2 — writer's operating contract

kancil is a steering-ticket experiment CLI for AI-assisted Kaggle
projects. Everything below is read from source at the commit above.
Config: `kancil.yaml` at the project root. State: `.kancil/`.
Discover the live surface: `kancil commands --json`, `kancil --help`.

## Order of operations (the gate chain)

1. `kancil setup` — guided wizard. Checks prereqs, detects Kaggle,
   scaffolds dirs + config + Claude slash commands. Prints the exact
   next-step order. `--domain` injects a domain pack (cv, tabular,
   llm-reasoning, audio, asr, nlp, simulation, llm-training).
2. `kancil bootstrap <slug|URL>` — cold-start for competitions:
   init → research → rules-solve → audit → spec → queue. Resumable
   via `.kancil/bootstrap_state.json`; research failures never block.
3. `kancil audit` — row counts, missing values, types. Run before the
   first experiment; assess warns until an audit exists.
4. `kancil data add <id> --desc <what>` — register data versions.
   Fingerprinted; drift surfaces in assess and `data drift`.
5. `kancil next-id --reserve` — claim the next id. Never guess ids.
6. `kancil new <id> -t '<title>'` — steering ticket + experiment doc.
   Refuses existing ids. Copy a base with `--base`.
7. `kancil review <id>` — structural gate (placeholders, empty
   sections, missing files). PASS writes a stamp with a docs hash.
   Implementation before a PASS is blocked: `run` exits 2, `guard`
   exits 2 for the hook protocol.
8. Implement. Then `kancil eval <id>` — discovers outputs
   (`output/<id>*` flat or per-dir), records results via
   `results --set`, annotates parity, compares vs base (advisory),
   auto-syncs the queue, pushes on verdict transitions.
9. `kancil stage <id>` — git add exactly this experiment's files.
10. Commit. `kancil submission add ...` only when a submission exists.

## The HIGH porcelain verbs (non-interactive by contract)

- `next` — session brief: delta since assess, queue head, board,
  guard blocks, one recommended action. Exit 2 = implementation
  blocked.
- `handoff` — successor brief: loops, jobs, queue, last verdicts,
  notes, error reports. Exit 2 = stale loop (fix: `loop --doctor`).
- `doctor` — read-only diagnostics: config keys, stale review stamps,
  orphans, stale loop PID, submission-gap divergence. Zero writes.
- `run <id>` — gated driver, checkpointed to `.kancil/run/<id>.json`:
  preflight (review PASS or exit 2) → running (optional `--command`
  as a detached job, one armed wait) → eval → stage → done. Resume
  re-invokes and skips done phases; `--reset` clears. Empty-eval
  (no outputs, no results) exits 1 with an `error-exp` pointer.
- `ship <id>` — eval → quota precheck → dry plan → stage → commit →
  submit → ledger. NEVER spends quota without `--yes`: the dry plan
  prints and exits 1. Quota exhausted exits 75.
- `setup`, `bootstrap` — see the order above.

## The loop (autonomous route)

`kancil loop --prompt prompts/auto.md --iteration-timeout 1800`

- The prompt file is piped into `claude -p`; skip-permissions is the
  default for prompt loops (`--permissions` opts out). `{iteration}`
  in the prompt is substituted each pass.
- Loop verbs: `--init-prompt` (creates prompts/auto.md + verified
  launch commands — run BEFORE claiming a loop is started),
  `--status` (VERIFY, never assume), `--stop` (set the sentinel),
  `--doctor` (reset stale state), `--takeover` (replace live rivals).
- Stop behavior: each iteration's env carries `KANCIL_STOP_FILE` and
  `EXP_MANAGER_STOP_FILE`, both naming `.kancil/loop_stop`. The agent
  touches that file when its work is done; the loop exits cleanly
  after the current iteration instead of starting another. The
  sentinel is checked at the loop top, during sleeps, during backoff,
  and during job waits (1s ticks).
- `--iteration-timeout N`: an iteration over N seconds is killed as a
  PROCESS GROUP (wrapper + session + descendants); the iteration
  records exit 124. A hung `claude -p` otherwise blocks forever.
- Failure taxonomy: exit 75 + `KANCIL_DEFERRED` on stderr = quota
  defer, retry after 00:00 UTC. Exit 2 alone is NOT a defer (argparse
  and gate blocks share it). Non-zero with EMPTY output = infra-fail.
  3 consecutive failures or any infra-fail streak escalates: backoff
  5/10/20/30 min (cap) with a push. A claude 429 sleeps until the
  parsed reset time (+60s, cap 6h).
- Adaptive cadence is default ON: results-change resets the interval,
  idle doubles it (cap max(4x, 120)), and the next session never
  starts sooner than half the duration EMA after the last one.
  `--no-adaptive` restores the fixed interval.
- Pipeline mode (`--pipeline`): an iteration that leaves a detached
  job running gets ONE prep pass (env `KANCIL_WAITING_JOB`), the loop
  watches the job exit file, and chains the next iteration the moment
  the job exits. The interval governs idle only.
- Persistent form (survives session close): `loop schedule --every
  30m|3h|1d [--prompt ...]`, mechanical `loop tick`, `loop status`,
  `loop remove`, `loop claim --whoami`. Cross-project: `loops`,
  `loops kill [targets]`.

## Jobs and process hygiene

- `job start '<cmd>'` — run detached under the registry (auto id
  jobNNN). `job list [--status running]`, `job status <id> --tail N`,
  `job wait <id> [--timeout S]` (one armed wait — never poll-spam),
  `job stop <id>` (TERM → grace → KILL, whole group).
- `orphans` — find loop-tagged processes whose loop died (`--kill`
  to SIGTERM; claim-holders skipped unless `--ignore-claims`).
- `inflight` — live artifact claims: what other actors hold.
- `claim <path>` — advisory lock, exit 0 free / 1 held.
- `cron-doctor` — audit the crontab for silent-cron defect classes.

## Kaggle verbs

- `submit <id> --competition <slug>` — CSV submit + auto LB fetch
  (backoff polling; score recorded to results when it lands).
  `--skip-wait` inside loops: the in-loop wait is auto-skipped (the
  paid session must not burn on polls; scheduled watchers record).
  `--kernel USER/SLUG [--version N]` submits a kernel for code
  competitions; the sandbox-parity gate then runs AUTOMATICALLY when
  `output/<id>.tar` exists — a parity crash aborts before quota is
  spent. `--policy auto` engages the ship-policy gate: champion
  needs `--beat-delta` + `--noise-floor`; probe needs `--question` +
  `--expected-band`, capped at 2/day, refused inside freeze windows.
- `kaggle-submit --username U --competition C --experiments e1,e2` —
  full code-comp pipeline, 5 steps: upload weights → verify datasets
  → generate kernel metadata → push kernel → wait + submit. Returns
  exit 75 when quota blocks: the submission.csv is already
  downloaded — resubmit it directly after 00:00 UTC WITHOUT re-pushing.
- `kaggle-weights <id> [--update]` — upload/verify weight datasets.
  `kaggle-kernel` / `kaggle-dataset` — scaffold folders.
  `kaggle-kernel-meta` — kernel-metadata.json with weights wired in;
  pass `--accelerator` explicitly (a bare GPU enable defaults to P100
  server-side; comps requiring T4x2 reject with a body-less 400).
  `kaggle-verify-tar <tar>` — raw-exec sandbox-parity check standalone.
  `kaggle-skills` — live capabilities of installed Kaggle plugins.
- `submission add --version V --oof X --lb Y|pending --method M
  --experiments e1,e2 [--purpose upgrade|info] [--local-h2h '2-18
  vs exp053_ref'] [--same-config-as GROUP]` — ledger row
  (.kancil/submissions.jsonl). `submission list` renders the
  OOF→LB gap trend. `submission quota --competition C` — used vs
  remaining for the UTC day (default limit 5 unless overridden).
  `submission backlog add --exp E --axis A [--expected-band ...]` —
  queue distinct variants; `submission backlog pop` drains one.
- `probe lb new --variable 'THE one changed thing' --question Q
  --baseline B [--max-per-day 2]` — arm a single-variable LB probe
  (budget-guarded). `probe lb <id> --lb S [--exp E]` — record the
  measurement; the verdict and delta land in the ledger + notes.
  `probe lr <id>` — scaffold an LR sweep. `probe epochs <id>
  --reference R` — honest probe-length verdict vs the reference's
  phase transitions.
- `research <query> --current <slug>` — scout similar past
  competitions + top kernels; report to
  `.claude/references/competition_research.md`; a forum fetcher, if
  probed, is named BEFORE any web fallback.
- `discussions --competition C` — sweep the forum, digest new posts
  to notes, flag anomaly posts worth pricing.
- `blog draft` — seven-point walkthrough from recorded state;
  `blog prompt` — the standalone draft contract.

## Verdicts and evidence

- Verdicts: WIN / LOSS / NEUTRAL, plus INVALID by manual call only
  (`eval <id> --invalidate --reason '...'`; results stay on disk,
  flagged). Thresholds can be pre-registered: a locked WIN/LOSS
  expression (e.g. `>89.6`) makes the verdict COMPUTED from the
  metric; a contradictory agent-set verdict is refused without an
  explicit override plus reason. Verdict history is append-only.
- `results <id> --set KEY=VALUE ... [verdict] [--implies '...']` —
  the one write path. A WIN with no `--implies` analysis draws a
  directive: record the mechanism before moving on.
- Gates read first: `compare` (significance-aware delta),
  `lift` (direction-aware, --by-fold/--by-subgroup), `portfolio`
  (worst-case across evaluator variants), `validate-check`,
  `correlate` (local-vs-remote trust tiers), `replica audit`
  (instrument drift > 1e-6), `eval-contract` (acceptance criteria
  without running), `error-analysis`, `cookbook` (regenerates from
  WIN implies-lines).

## Plan, monitor, train

- `queue add <id> --priority N [--base B]`, `queue next --claim`
  (atomic), `queue start/done/remove`, `queue list [--json]`.
  `note '...' [--exp E] [--pin]`. `directive add '...'` — operator
  channel; the loop consumes directives into its next iteration.
  `target --set metric=value`. `axis` — sweep-space registry.
- Read views: `assess` (the loop's first read: drift, directives,
  new results, verdict synthesis), `board --json`, `status <id>`,
  `list`, `dashboard`, `progress`, `viz`, `diff A B`, `graph`,
  `search`, `compare`, `report`, `drilldown <id> --json`.
- Training infra: `make-folds` (deterministic fold columns; refuses
  unaudited projects), `folds` (per-fold status + multi-GPU launch),
  `farm` (train a farm from farm.yaml), `blend` (non-negative hill
  climb over member OOFs), `eda` (structured report), `derive`
  (EDA → farm.yaml), `gpu` (pool status/reap), `trial`, `axis`.

## Exit codes and failure modes

| exit | meaning |
|------|---------|
| 0 | ok |
| 1 | error (missing file, submit failure, ship dry plan, empty eval) |
| 2 | usage or GATE BLOCK: uninitialized project, review gate open, bad id, probe budget reached; `next` when blocked; `handoff` on stale loop |
| 75 | quota defer (EX_TEMPFAIL): ship precheck, submit 400-classified-quota, kaggle-submit; stderr carries `KANCIL_DEFERRED` |
| 124 | iteration timeout (process group killed) |

- Quota is spent only by `ship --yes` or an explicit submit. Unknown
  quota (network/auth) refuses instead of guessing.
- A submit 400 needs classification: quota (UTC-day count) vs kernel
  constraint (GPU type — retry via SDK for the response body).
- Kernel push 409 = slug conflict: change the slug, don't retry blind.
  Kaggle may derive a different slug from the title; the server-side
  slug is what gets recorded.
- Dataset verification that couldn't RUN (network) means retry, never
  re-upload.
- Notifications push on transitions only (verdict change, escalation,
  heartbeat). Configure with `notify config <topic>`, test with
  `notify test`; severities all/loss/win/user_action.

## Writer route (rumpun)

Route: `kancil loop --prompt {prompt} --iteration-timeout 1800`.
The prompt file must tell the agent to `touch "$KANCIL_STOP_FILE"`
when its work is done — the loop then stops after that iteration.
Every verb named in this file exists in the parser at the commit in
the frontmatter; the pinned registry is `kancil commands --json`.

## Verb inventory (all live at source-commit)

- lifecycle: setup, bootstrap, init, new, quick, next-id, review, eval, stage, guard, organize
- monitor: list, status, dashboard, board, assess, progress, viz, drilldown, report, diff, graph, search, compare, cookbook, swarm-card, swarm-models
- evidence: results, lift, trace, eval-contract, correlate, replica, replica-audit, portfolio, validate-check, error-analysis
- planning: queue, note, claim, audit, data, cockpit, poll, directive, target, axis, inflight, orphans
- automation: loop, loops, job, cron-doctor, swarm-init, swarm-fight, swarm-add, swarm-stop, swarm-next, swarm-status, swarm-say, swarm-shared
- kaggle: blog, kaggle-kernel, kaggle-dataset, kaggle-skills, kaggle-weights, kaggle-verify-tar, kaggle-kernel-meta, kaggle-submit, submit, research, probe, discussions
- submission: submission, submission-watch
- sim: slots, ladder-history, episodes, rules-solve, opponents
- training: make-folds, folds, farm, blend, eda, derive, gpu, trial
- session: next, handoff, doctor, skills, run, ship
- misc: notify, dashboard-port, commands

Nested subcommands (top-level + sub): loop schedule/tick/status/remove/claim; loops kill; job start/list/status/wait/stop; queue add/list/next/start/done/remove; data add/list/impact/drift; directive add/list; notify status/off/config/test; probe lb/lr/epochs; submission add/list/quota; submission backlog add/list/pop; replica register/list/audit; blog draft/prompt; episodes fetch/postmortem/hypothesize/due/scheduled; skills list/audit.
