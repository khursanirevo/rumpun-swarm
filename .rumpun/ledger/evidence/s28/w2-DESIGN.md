# DESIGN.md — rumpun

Status: design in progress, nothing implemented. Working dir empty until scaffolding.
Started: 2026-09-14. Repo target: `khursani/rumpun`.
Predecessor: kancil at `/mnt/data/work/kancil` (same author; NOT self-evolving; pattern
source, not a fork). This file is the canonical record of the design discussion.
Any agent joining the discussion reads this file plus the kancil references below.

## 1. What rumpun is

A CLI that initializes the current folder to bootstrap a self-evolving multi-agent
swarm. Agents mix closed and open models (Fable, Opus, GLM 5.2, GLM 5.3, GPT Astra,
GPT Sol, Codex Sol), all configured from YAML. YAML is the first-class citizen.

Self-evolving means: season lifecycles are not strict. Every season the YAML is
rewritten when evidence proves a methodology change is needed. The pipeline, the
agents, the model mix, the interaction mode, the prompts — all can change between
seasons. Purpose: break plateaus by changing approach.

## 2. Vocabulary

| Term | Meaning |
|---|---|
| Rumpun | entire swarm (project name) |
| Benih | seed/base agent definition |
| Tunas | newly generated agent (offspring) |
| Cabang | evolutionary branch |
| Akar | shared memory / knowledge base |
| Rimba | execution environment |
| musim | season (proposed) |
| tuai | harvest, season close (proposed) |
| evolusi | the evolution step producing next season (proposed) |
| baka | lineage (proposed) |

The first six are fixed by the author. The last four are proposals under discussion.

## 3. What carries over from kancil (verified in its source, 2026-09-14)

| kancil mechanism | rumpun use |
|---|---|
| `src/kancil/routes.py` | route detection: which model routes this machine can spawn. Family label from resolved command + env, never the binary name. Env-strip of `ANTHROPIC_*` recovers the login route. Never log token values. |
| `swarm.py` + `proc.py` | agents are one-shot children in own process groups. No daemon. Completion = exit file. Liveness = pid + proc start time (PID-reuse guard). |
| workspace contract | per-agent dir: `prompt.md`, `prompt-include.md`, append-only `discovery.md`, `state.json`, `results/` |
| lanes + knowledge staging | one mechanism per agent; none/partial/full prior knowledge; negative examples rendered as "strong AND different" |
| `campaign.py` `campaign_memory()` | harvest fields: winners, open items, ceiling evidence, unexplored axes |
| season design doc honesty contract | liveness verified, never trusted; stalled fights surfaced |

Leave behind: all Kaggle machinery (folds, submissions, ship policy, opponents, blend)
and kancil's fixed pipeline. Rumpun is domain-agnostic; the task contract lives in
season YAML. kancil's known open defects are listed in its `REPO_ANALYSIS/00-INDEX.md` —
do not copy them.

Kancil references worth reading:
- `doc/02_architecture.md`, `doc/glossary.md`
- `INTERACTIVE_FEATURE_DISCUSSIONS/swarm-season-discussion-design.md`
- `REPO_ANALYSIS/00-INDEX.md`

## 4. Folder layout (`rumpun init`)

All project state sits in one hidden directory at the target root:

```
.rumpun/
  rumpun.yaml      # campaign goal, autonomy stages, budget cap, routes
  musim/           # one YAML per season: s1.yaml, s2.yaml, ...
  benih/           # seed agent definitions
  akar/            # append-only knowledge base, one record per finding
  prompts/         # base/ + per-season prompt templates
  rimba/           # per-season workspaces (gitignored)
```

Committed except rimba/: git history over `.rumpun/` is the evolution ledger.
The directory is invisible to a plain `ls`, but it is NOT a .omc-style cache:
.omc-style state is disposable and ignored; this state is the evidence chain
behind P11/P12 citations and audit. Relative paths in season YAML (prompts/,
akar citations, rimba workspaces) resolve against `.rumpun/`.

## 5. Season YAML (the one file evolusi rewrites)

```yaml
# musim/s3.yaml
id: s3
parent: s2                      # cabang lineage
goal: "<verbatim, immutable within a campaign>"
metric: oof_auc
target_delta: 0.0015
mode: fight                      # fight | collab
collab:                          # read only when mode: collab
  lane: rimba/s3/shared/messages.jsonl
  share: [discovery, plan]
  merge: per_iteration
methodology:
  approach: "decorrelated-member hunt"
  evidence: ["akar/2026-09-14_ceiling_s2.jsonl#L4"]   # why this approach
  pipeline:                      # see section 7
    - phase: analyze
      agent: analyst
      prompt: prompts/s3/analyze.md
      writes: errors.jsonl
    # ... rank_gaps, hypothesize, plan, falsify, execute, evaluate
benih:
  - name: a1
    route: glm-5.2              # resolved by route probe at spawn
    lane: gbdt
    prompt: prompts/gbdt.md
    knowledge: full             # none | partial | full akar staging
    budget: {minutes: 240}
stop:
  on: [all_exited, stall_minutes: 45, budget_exhausted]
```

Schema rule: a methodology change with a missing evidence citation, or a citation to a
file that does not exist, refuses to launch at `rumpun start`.

## 6. Evolution loop

1. `rumpun start` spawns the season from `musim/sN.yaml`.
2. Agents run the pipeline / fight. Discoveries append per agent; collab lane optional.
3. `rumpun harvest` closes the season: verdicts WIN/LOSS/NEUTRAL/INVALID, implies lines,
   open axes, ceiling evidence append to `akar/`.
4. `rumpun evolve` runs an evolver agent: reads `akar/` + `musim/sN.yaml`, emits
   `musim/sN+1.yaml` plus an evolution record (what changed, why, evidence cite,
   expected outcome band).
5. Guardrails: every methodology change cites akar evidence; goal and metric immutable
   without human approval; budget caps enforced; expected outcome band stated per season.

Decision made: early seasons run `evolve` as a proposal; `rumpun evolve apply` commits.
Auto-apply switches on only after the harvest format proves itself over manual seasons.
Decision made: CLI verbs are English over Malay nouns (kancil style); reversible choice.

Evolution escalation rule (evidence bar rises with each step):
1. retune — same pipeline, different parameters (top_n, routes, staging)
2. reorder/drop — change or remove phases
3. switch pipeline — replace the workflow entirely; strongest citation requirement;
   the switch itself is a headline record in akar

Invariant: engine code stays fixed during a campaign. Only YAML evolves. A season
needing a phase type the engine lacks is a human-gated code change.

## 7. Pipeline layer

A season's workflow is YAML-declared as a phase pipeline. Example (the author's
reference pipeline):

```yaml
pipeline:
  - phase: analyze        # error analysis on current best output
    agent: analyst
    writes: errors.jsonl
  - phase: rank_gaps      # top points worth resolving
    top_n: 3
    reads: errors.jsonl
    writes: gaps.yaml
  - phase: hypothesize    # one hypothesis per gap
    per: gap
    writes: hypotheses.yaml
  - phase: plan           # experiment testing each hypothesis
    writes: experiments.yaml
  - phase: falsify        # kill criterion written BEFORE execution
    must_precede: execute
    writes: falsification.yaml
  - phase: execute
    agents: benih
  - phase: evaluate       # results vs committed falsification criteria
    writes: verdicts.jsonl
loop:
  until: stop.rules_met
```

Mechanics:
- Phases exchange artifact contract files (`errors.jsonl`, `hypotheses.yaml`, ...).
  The engine checks the contract exists before the next phase starts. Resumable, auditable.
- `must_precede: execute` is a schema rule: the kill test is committed before any
  experiment runs. Positive results cannot redefine themselves after the fact.
- Engine ships a fixed primitive library: analyze, hypothesize, plan, falsify, execute,
  evaluate, spawn, share, harvest + scheduler. Evolusi composes; it never edits its
  own executor.

## 8. Interaction modes

| | fight | collab |
|---|---|---|
| workspaces | fully isolated | isolated + shared lane file |
| communication | none until tuai | append rows `{ts, agent, kind, body}` to the lane; re-read per iteration |
| knowledge flow | akar staging at spawn | akar staging + live lane |
| kancil precedent | s1–s6 fights, `shared_lane: false` | `shared/messages.jsonl` mechanism, verified |

Mode trade-offs the evolver weighs, with akar signals for both directions:

| Mode | wins by | fails by | flip evidence |
|---|---|---|---|
| fight | diversity, independent confirmation | duplicated work | duplicate-discovery rate high, re-deriving closed walls |
| collab | compounding knowledge, no rework | herding | distinct-approach count drops, lanes converge |

Extensions in order: (1) mid-season adapt triggers declared in season YAML, e.g.
`adapt: [{when: duplicate_work_gt 0.5, set: {mode: collab}}]`; (2) hybrid pods — mode
per cabang instead of per season.

## 9. Prompt tracking (three levels)

1. **Templates**: `prompts/base/<phase>.md` + per-season overrides `prompts/sN/<phase>.md`,
   git-tracked. Season YAML names the path explicitly.
2. **Rendered instance**: per execution, `rimba/sN/<ts>_<phase>_<agent>/prompt.md`
   (immutable, exactly what the agent saw, injections included) + `prompt-meta.yaml`
   (template path, template sha256, season yaml commit, input artifact hashes,
   akar excerpts cited, route, iteration).
3. **Ledger**: append-only `runs.jsonl` row per execution: run id, season, phase, agent,
   template hash, iteration, exit, artifact, minutes.

Collab mode re-renders per iteration; each iteration gets its own run directory.
Query verbs: `rumpun prompt show <run>`, `rumpun prompt diff s2 s3 <phase>`,
`rumpun runs --phase hypothesize`. Prompt evolution = evolusi edits templates,
cited like methodology changes; season-over-season prompt diff is a git diff.
Template is intent; rendered instance is fact.

## 10. Build order

1. `rumpun init` + templates + `rumpun.yaml` schema
2. route probe (`rumpun models`), ported from kancil `routes.py`
3. `season start` / `board` / `season stop`: spawn, exit files, verified liveness,
   stall detection,
   mode-aware (lane file only in collab)
   -> SHIPPED in s1, verdict WIN 2026-09-14 (fight mode; collab lane file still open)
4. akar ledger + `harvest` (manual verdict entry first)
   -> SHIPPED in s2, verdict WIN 2026-09-14 (akar writer, harvest verb, dogfooded on s2)
5. `evolve plan` / `evolve apply` v0 SHIPPED in s2 (deterministic draft, lint-gated apply):
   evolver drafts next season YAML with mandatory
   citations, human applies

## 11. Open questions

| # | Question | Status |
|---|---|---|
| Q1 | Fresh codebase vs fork of kancil | RESOLVED: fresh codebase, ratified 2026-09-14 |
| Q2 | GLM 5.3 / GPT Astra route availability on this machine | RESOLVED empirically 2026-09-14 by `rumpun models`: glm proxy + claude login routes present; codex cache exposes 7 slugs incl. gpt-6-astra and gpt-5.6-sol; glm-5.3 model-level availability needs the quota-spending --probe (operator opt-in) |
| Q3 | Codex Sol role in rumpun seasons | joined as design reviewer 2026-09-14; in-season route role open |
| Q4 | musim / tuai / evolusi / baka naming | ACCEPTED as working names, ratified 2026-09-14 |
| Q5 | auto-apply threshold for evolusi | RESOLVED by P33 staged autonomy, ratified 2026-09-14 |

## 12. How to contribute to this discussion (any agent)

- Read this file top to bottom plus the kancil references in section 3 before proposing.
- Propose changes as an entry under a `## Proposals` appendix: what, why, evidence cite,
  which section it amends. Do not rewrite decided sections unilaterally.
- Decisions land in the relevant section with a "Decision made:" line; the proposal
  appendix entry then marks it accepted or rejected with reasons.
- Style: short sentences, tables over prose lists, evidence-cited claims, no mock data.

## 13. Operator experience (P36 ratified 2026-09-14)

The operator question is not "what did the agent say" but "is the swarm healthy,
honest, progressing — and do I approve this evolution". Existing trace tools
(AgentOps, LangSmith, Langfuse; see AIMultiple 15-tool roundup) answer per-call
developer questions; none model seasons, evolution ledgers, or evidence citations.
Research base: the SAT transparency model (Chen et al. 2014: show activity+cause,
rationale+evidence, projection+uncertainty; 2026 decade review: builds calibrated
trust, while transparency volume alone has mixed effects) and Graph of Trace
(ACL 2026 demo: structured trace views beat raw logs for interpretability in a
user study).

Data contract first: one harness-owned season snapshot plus an append-only event
ledger, computed by the harness outside agent-writable paths. Terminal, JSON, and
HTML views render only from that snapshot; views are derived and never
authoritative. Reports name their source hashes and display STALE when ledger
hashes move.

Provenance label on every displayed value:

| Label | Meaning | Examples |
|---|---|---|
| [H] | harness-observed | exit codes, wall-clock minutes, content hashes, git tree SHA, DAG transitions, wall-injection set |
| [A] | agent-authored | verdicts, discoveries, confidence, citation relevance, git author fields |
| [D] | derived from stated inputs | success status (policy expression shown), forecasts |

Color may supplement labels, never replace them. Evidence citations stay [A]:
the harness checks locator resolution and content hashes; it never establishes
that evidence supports the claim. If agents share the harness Unix identity,
[H] means observed, not tamper-resistant; the threat model states this limit.

Surfaces, in priority order (all local, no SaaS, ssh-safe):

| Priority | Surface | Shape |
|---|---|---|
| 0 | status snapshot + --json | stable read model every view consumes |
| 1 | `rumpun board` | non-interactive terminal snapshot by default; --watch TUI optional |
| 2 | season report | self-contained static HTML per season, deterministic, git-diffable |
| 3 | local web server | deferred; 127.0.0.1, read-only, no unique control actions |

Board panels (default view): action queue, season identity with pinned revisions,
DAG critical path, node states, budget and time, recent harness events, audit
disagreement, pending evolution, integrity warnings. The default view answers, in
order: what needs me, is it progressing, what changed, on what evidence, what
dissent remains, can I stop or reverse it.

Per-stage foreground (SAT mapping; higher autonomy needs stronger provenance and
exception reporting, not more routine detail):

| Stage | Foreground |
|---|---|
| manual | approval queue, exact diff, evidence, dissent, rollback, policy checks |
| panel | eligibility, sealed verdicts, quorum, reconciliation delta, exceptions |
| free | policy envelope, applied changes, integrity events, drift, sampled audits, rollback readiness |

Progress and stall: stall_minutes must key on harness-observed durable progress:
node state change, new artifact content hash, accepted checkpoint, dependency or
tool completion. Heartbeats, identical log lines, and mtime-only changes do not
count. Node states: waiting, idle, suspected_stall, stalled, deadlocked
(unfinished graph with no runnable path).

Alerts: an alert is a new actionable state; everything else is a digest.
Immediate: approval required, policy boundary crossed, ledger or artifact
tampering, impossible quorum, unresolved material dissent, deadlock, retries
exhausted, invariant failure, budget exhaustion stopping required work,
blast-radius excess, rollback unavailable. Digest: completions, expected retries,
threshold warnings, wall review dates, non-blocking dissent, drift. Quiet:
heartbeats, log lines, expected waiting. Ping once on open, update the same
incident, re-ping only on escalation, record resolution silently.

## Proposals

### P1 — evolution loop stability (amends section 6) — claude, 2026-09-14

- **Oscillation**: mode flips fight→collab→fight every season because each flip's failure
  evidence triggers the reverse. Fix: interaction-mode changes carry a minimum TTL of two
  seasons unless a catastrophic threshold fires; the evolution record must cite the previous
  evolution record and state what is different this time. Akar gains an oscillation counter.
- **Evidence gaming**: the evolver cites evidence it wrote itself. Fix: akar records carry a
  writer field; only records with `writer: harvest` count as valid citations for methodology
  changes. Schema check rejects self-authored citations.
- **Noise-floor wins**: a target_delta below the noise floor produces cosmetic WIN verdicts
  (kancil glossary: σ ≈ √(p(1-p)/N)). Fix: season YAML declares an estimated noise floor;
  evaluate downgrades a WIN below it to NEUTRAL with the reason recorded.

### P2 — pipeline contract enforcement (amends section 7) — claude, 2026-09-14

- A phase can write a malformed artifact, starving the loop. Fix: per-artifact schema
  validation at the phase boundary; the retry policy (retry N times, then halt) is declared
  in the phase entry.
- `loop.until` plus unmet stop rules can run forever on wall-clock time while per-agent
  budgets stay unspent. Fix: season-level wall-clock budget in `stop.on`.
- `per: gap` fan-out with a rising top_n explodes the execute phase. Fix: `max_concurrent`
  and a per-season cap on total experiments in season YAML.

### P3 — falsification quality (amends section 7) — claude, 2026-09-14

- An agent can commit a vacuous kill test ("the script runs"). Fix: falsification.yaml has
  a required schema: metric, threshold, and the concrete prediction that dies. evaluate
  must quote the committed criterion verbatim in verdicts.jsonl next to the result.

### P4 — collab lane hygiene (amends section 8) — claude, 2026-09-14

- Lane flooding: one agent drowns the lane, context bloat for every reader. Fix: per-row
  size cap, per-agent lane quota, per-iteration read cap (dedupe + last N rows).
- Lane poisoning: one wrong "finding" correlates the whole swarm; fight mode contains this
  failure, collab amplifies it. Fix: lane rows are typed and marked unverified until tuai;
  the collab block declares `trust: leads` and agent prompts must treat lane rows as leads,
  not facts.
- Adapt-trigger flapping: duplicate_work hovering at 0.5 flips mode repeatedly mid-season.
  Fix: hysteresis, the trigger fires only after two consecutive checks past the threshold.

### P5 — akar injection budget (amends section 9) — claude, 2026-09-14

- Akar grows unboundedly; `knowledge: full` injection bloats every render. Fix: benih
  knowledge staging declares a token budget and retrieval is relevance-ranked excerpts.
  Harvest compaction: closed seasons are summarized into `akar/summary/` by the harvest
  writer, originals stay append-only.

### P6 — route staleness at spawn (amends section 5) — claude, 2026-09-14

- A route probed green at init dies at spawn (expired token). Fix: probe again at spawn and
  fail fast naming the benih; optional `fallback_route:` per benih resolved the same way.

### P7 — evolution review gate (amends section 6) — claude, 2026-09-14

- The evolver approves its own season plan; same-model blind spots pass unchallenged.
  Fix: `evolve --apply` requires a reviewer pass by a different model family than the
  evolver, reviewer verdict recorded in akar. Mirrors the kancil lesson that three same-type
  agents re-derived one closed wall: correlated reviewers correlate mistakes.

### P8 — directives channel for the human seat (amends section 6) — claude, 2026-09-14

- kancil ported directives in name only; rumpun never defined them. Fix: `rumpun direct
  "text"` appends to `akar/directives.jsonl`, consumed at the next phase boundary. Per the
  kancil honesty contract, nothing is injected into a running process; the artifact records
  pending versus consumed.

### P9 — cost ledger and campaign cap (amends sections 9 and 5) — claude, 2026-09-14

- runs.jsonl tracks minutes only. Fix: record tokens and cost when the route reports them;
  rumpun.yaml holds a campaign cost cap that `start` checks before spawning a season. This
  encodes the operator rule "state what the run IS before burning quota".

### P10 — replay determinism check (amends section 10, build order) — claude, 2026-09-14

- Season reproducibility is claimed but untested until a season runs. Fix: `rumpun replay
  sN --dry` re-renders all prompts from season YAML plus template hashes without spawning;
  byte-identical re-renders prove the record is complete. Cheap to build, catches provenance
  gaps before they cost a season.

Status: P1-P10 are the host agent's interim pass, added 2026-09-14 while the Codex critique
was blocked by quota (see `proposals/codex-2026-09-14-s1.md` — the run hit the ChatGPT
usage limit; raw log preserved). Codex Sol's independent pass is pending quota reset.

### Codex Sol pass, 2026-09-14 (P11-P32 + 34 edge cases) — author: codex/gpt-5.6-sol, verdicts: claude

Raw critique: `proposals/codex-2026-09-14-s1.md` (full session log, 32,093 tokens used).
Shape: 34 edge cases across sections 5-9 plus proposals P11-P32. Verdicts below; items
marked * need author ratification before amending decided sections.

| Proposal | Verdict | Note |
|---|---|---|
| P11 immutable evidence refs | ACCEPT | `akar:<record-id>@<sha256>` supersedes the `#L4` sketch; line numbers become display metadata |
| P12 causal change control | ACCEPT* | one `primary_change` per normal season; pipeline-switch keeps its named bundle class under the escalation rule |
| P13 metric-specific uncertainty | ACCEPT | replaces P1's Bernoulli formula; uncertainty estimator declared beside each metric definition |
| P14 typed akar records | ACCEPT | observation / verdict / hypothesis / proposal + derivation edges; subsumes P1's `writer: harvest` rule |
| P15 content-addressed artifacts | ACCEPT | atomic rename, input/output hashes, typed recovery policies replace P2's unconditional retry |
| P16 structured falsification | ACCEPT | strengthens P3: comparator/metric/threshold/dataset/confidence, sealed before execute, consequences kill/revise/retain/inconclusive |
| P17 evaluator independence | ACCEPT | merges with P7: proposer != executor != evaluator, enforced at falsify, evaluate, and evolve review |
| P18 defer live mode switching | ACCEPT | MVP keeps season-level mode only; adapt triggers and pods go behind an experimental flag |
| P19 safe mode transitions | ACCEPT | ships with adaptation later: pipeline barriers only, monotonic `mode_epoch`, lane close + full rerender |
| P20 prompt trust zones | ACCEPT | engine rules / template / untrusted quoted data; provenance per injected block; rejects unbounded interpolation. New requirement, not previously covered |
| P21 deterministic prompt budgets | ACCEPT | merges with P5: explicit token ceilings, versioned selection rules, omissions recorded in prompt-meta |
| P22 overlay composition | ACCEPT* | MVP keeps explicit per-season override files because they are diffable; P27 lint warns on stale overrides; overlay composition lands post-MVP |
| P23 spawn-scoped route checks | ACCEPT | merges with P6: probe TTL, preflight before each spawn batch, fingerprint change halts new work |
| P24 budget hierarchy + stop state machine | ACCEPT | run/agent/phase/season/campaign/provider budgets, monotonic usage ledger, stop precedence, reserved finalization budget |
| P25 liveness vs activity vs progress | ACCEPT | stall detection keys on progress events, not process existence; kancil pid+start-time check retained for liveness |
| P26 replayable run manifest | ACCEPT | extends P10: freeze season YAML, rendered prompt bytes, route identity, engine version, dependency hashes |
| P27 `rumpun lint` | ACCEPT | one preflight boundary run by `start` and `evolve --apply`; added to build order step 1 |
| P28 hash-chained ledgers | ACCEPT* | monotonic seq numbers + chained record hashes from day one; signature verification deferred |
| P29 cut auto-apply from MVP | ACCEPT* | stricter than the earlier decision (which tied auto-apply to harvest-format maturity); explicit apply throughout MVP |
| P30 regression + control seasons | ACCEPT* | MVP: pinned-task invariant checks inside harvest; full unchanged control seasons only when drift is suspected |
| P31 narrow MVP pipeline machinery | ACCEPT* | see modification below; scope decision, needs ratification |
| P32 secret + sensitive-data controls | ACCEPT | env allowlists per route, redaction before any persistence, credential-pattern rejection, redaction events logged without values |

P31 modification (keep the author's reference workflow): the MVP ships the fixed
sequential reference pipeline (analyze, rank_gaps, hypothesize, plan, falsify, execute,
evaluate) because every phase reuses the same execution primitive. What gets narrowed is
the workflow MACHINERY, not the pipeline: `loop.until`, `per: gap` fan-out, mid-season
adapt triggers, and arbitrary pipeline replacement are all post-MVP.

Edge cases adopted without their own proposal number: require YAML 1.2 and reject
non-string mapping keys (`stop.on` parses as boolean under YAML 1.1); reject `../` and
symlink escapes in artifact paths; record every dead cabang with termination reason and
cost to prevent survivor bias; single-writer locked appends for the collab lane (concurrent
appends corrupt JSONL); structured approach classification so distinct-approach counts
resist wording games; hash rendered prompt bytes, not just templates.

End state of the P1-P10 critique: P1 formula superseded by P13, P1 writer rule subsumed
by P14, P2 retries replaced by P15 typed recovery, P3 strengthened by P16, P5 merged into
P21, P6 merged into P23, P7 merged into P17. P4, P8, P9, P10 stand as written.

Q3 status update: Codex Sol joined as design reviewer on 2026-09-14 and delivered
P11-P32. Its role inside rumpun seasons (route for benih, evolver, or reviewer) is still
open; P17 and P7 make a different-family reviewer mandatory regardless.

### P33 — staged autonomy via cross-family audit panel (amends P29; author: khursani, formatted: claude, 2026-09-14)

Author directive: full autonomy is the goal of self-evolution; a permanent human apply-gate
defeats the purpose. P29 is amended from "explicit apply throughout MVP" to staged autonomy.

**Mechanism — the `audit` phase at every season boundary:**

- Panel of one agent per model family (e.g. fable, glm, gpt-5.6-sol), families declared in
  rumpun.yaml. Mandatory family diversity per P17.
- Each member independently reviews the proposed season YAML diff against: harvest records,
  the last K evolution records, and pinned invariants. Blinded: members submit verdicts
  before seeing each other's. Structured verdict: approve / reject + reasons, every reason
  citing akar evidence.
- Panel checks target COMPOUNDING error specifically, not single-diff sanity:
  goal-drift via pinned tasks (P30), evidence-chain integrity (P28), escalation-rule
  compliance (P12), falsify-phase presence, metric-to-goal tracking (proxy drift).

**The honest catch — detection is not containment.** A panel that says "reject" without an
automatic response still lets error compound. So autonomy requires three legs:

1. DETECTION: the audit panel above (judgment calls).
2. HARD INVARIANTS the panel cannot waive: goal immutable, campaign budget cap,
   falsify-required. Schema and lint enforce these before the panel is even consulted.
   No majority approves a goal change.
3. CONTAINMENT: on reject, automatic rollback to the last-good season tag (git),
   the rejected proposal recorded in akar as rejected (append-only, never deleted),
   campaign pauses; after N consecutive rejects, escalate to the human.

**Staged autonomy — the autonomy level itself evolves:**

```yaml
autonomy:
  stage: panel            # manual | panel | free
  promote_after: {clean_audits: 5}
  demote_on: {consecutive_rejects: 2}
  panel:
    families: [fable, glm, gpt-5.6-sol]
    rule: majority        # majority | unanimous
    blinded: true
  invariants: [goal_immutable, budget_cap, falsify_required]   # panel cannot waive
  on_reject:
    action: rollback_to_last_good
    escalate_after: {consecutive_rejects: 2}
```

- `manual`: every apply explicit (today's MVP default).
- `panel`: auto-apply IF the cross-family audit approves; rollback on reject.
- `free`: no audit, full autonomy. Reached only by promotion, demoted automatically.
- Promotion and demotion criteria are YAML, so the swarm earns its autonomy level from its
  own track record and can lose it. The governor is itself evolvable, which matches the
  project thesis.

**Costs and limits, stated:** the panel bills every season boundary across three families;
latency grows by one review round. A panel shares one akar, so context poisoning is still
possible — hash chains (P28) and invariants carry the hard part, the panel carries judgment.
Novel failure modes can pass any panel; invariants and demotion are the backstop.

Verdict on P29: SUPERSEDED by this proposal. Build order change: `manual` stage only for
MVP (unchanged effort), `panel` stage added to the post-MVP milestone list, `free` gated
on promotion criteria. Needs author ratification of the stage mechanics and the invariant list.

### P31 amendment — DAG ruling (author: khursani, recorded: claude, 2026-09-14)

Author intent: the pipeline is DAG-like, and reviewability is the priority — easy for a
human to review, easy for evolusi to update.

Ruling: the MVP ships a STATIC DAG scheduler.

- IN: acyclic phase graph in season YAML; bounded fan-out per node (`max_concurrent`);
  one artifact contract per edge; the graph is frozen for the season's entire duration.
- OUT (post-MVP): cycles (`loop.until`), mid-season adapt triggers, live pipeline
  replacement. These are the review killers: they change what the season is doing while
  it runs, which is exactly what a reviewer cannot hold in their head.
- This supersedes my earlier P31 modification, which deferred ALL fan-out. Bounded static
  fan-out returns to the MVP because a frozen DAG keeps its review cost flat: the graph is
  readable top to bottom, every edge names its contract, and nothing moves mid-season.
- Iteration moves across seasons: running the graph again with updated inputs is sN+1,
  proposed by evolusi with evidence. Evolution IS the loop; the season is one pass.
- Review surface: `rumpun graph sN` renders the DAG (mermaid) for one-glance review;
  P27 lint enforces acyclicity, edge-contract match, and per-node budgets before start;
  evolution diffs are graph diffs, kept small by P12's one-primary-change rule.
- Nice alignment: cabang works at two levels now — branches WITHIN a season (parallel
  hypothesis lanes in the DAG) and branches ACROSS seasons (lineage via `parent:`).

### P34 — node mutation grammar (author: khursani, recorded: claude, 2026-09-14)

Author confirmation: rumpun runs the static-DAG proposal, and self-evolution MUST be able
to add and remove nodes in the pipeline. Clarification of the P31 DAG ruling: the graph is
frozen WITHIN a season; node mutation BETWEEN seasons is the primary evolution act.

**What evolusi may do to the graph at a season boundary (all YAML, all cited):**

| Move | Meaning | Guard |
|---|---|---|
| ADD | instantiate an existing primitive as a new node, wire edges, declare contracts | edge contracts must type-check; lint acyclicity |
| REMOVE | delete a node | no remaining consumer of its artifact, or edges rewired first |
| REWIRE | change an edge's producer or consumer | producer `writes` schema must match consumer `reads` schema |
| RETUNE | change a node's parameters (top_n, max_concurrent, agent, prompt) | unchanged graph shape |

**The one hard boundary:** every node binds to a primitive from the fixed engine library
(analyze, rank_gaps, hypothesize, plan, falsify, execute, evaluate, share, harvest, audit).
Evolusi composes and recombines primitives freely. A node TYPE that no primitive implements
is a human-gated code change, never a mid-campaign YAML trick. Graph evolution is free;
the executor stays fixed. This is what makes arbitrary graph growth safe.

**Example evolution (git diff between seasons):**

```diff
 # musim/s4.yaml — after s3 harvest showed gaps.yaml quality was poor
   - rank_gaps:   { reads: errors.jsonl, writes: gaps.yaml }
+  - prior_art:   # NEW node: research primitive, checks akar before hypothesizing
+      primitive: research
+      reads: gaps.yaml
+      writes: priors.yaml
+      evidence: ["akar:s4-harvest@9f3ab2c"]   # cites the harvest finding
   - hypothesize: { reads: gaps.yaml, writes: "hypotheses/<gap_id>.yaml" }
```

```diff
 # musim/s5.yaml — after s4 ceiling evidence showed ensembling was exhausted
-  - blend:       { reads: "oof/*.npy", writes: blend.npy }
   - evaluate:    { reads: falsification.yaml, writes: verdicts.jsonl }
```

**Review and safety rails for graph mutation:** P12 keeps diffs small (add/remove IS the
primary_change of that season); P27 lint validates the new graph before start; the P33
audit panel reviews the graph diff as its core job; git is the graph history;
`rumpun graph sN --diff sN-1` renders before/after in mermaid.

Status: author approved the direction in this session; this entry records the grammar.
Build can proceed on the P31-DAG + P34-grammar basis once remaining ratifications land.

### P33 ratified (2026-09-14)

Operator answers, all six points decided:

- Panel: fable + glm + gpt-5.6-sol, majority rule (Q1).
- Verdicts: two-phase — blinded first, then one open reconciliation round; both transcripts
  append to akar (Q2).
- Audit scope: risk-based — audit when primary_change is add/remove/rewire/switch; pure
  retune seasons pass on lint alone; any rejection forces full audit the next season (Q3).
- Invariants stay exactly three: goal_immutable, budget_cap, falsify_required (Q4).
- Numbers: promote after 5 clean audits, demote after 2 consecutive rejects, pause on
  reject confirmed (Q5).
- Staging: MVP ships `manual` only; `panel` is the next milestone; `free` requires human
  promotion (Q6).

Decision made: P33 stands as amended by these answers. Stages: manual -> panel -> free,
promotion and demotion criteria declared in rumpun.yaml.

### P12 ratified + all open items closed (2026-09-14)

Operator: "follow all default" on the P12 decision points.

- Q1: unit of change = one node; its prompt, budget, edges are labeled controlled dependencies.
- Q2: bundle classes = pipeline_switch, emergency, rollback_restore, free_bundle
  (free_bundle approvable only by the audit panel at panel/free stages).
- Q3: baseline, expected band, rollback rule, evaluation window are REQUIRED per season,
  lint-enforced (operator quota rule encoded).
- Q4: attribution baseline = parent season best with its P13 uncertainty interval.
- Q5: hard veto — an undeclared change in the diff is an invariant hit, auto-reject.
- L1: fresh codebase confirmed. L2: musim/tuai/evolusi/baka accepted as working names.

Decision made: P12 stands as amended. With this, section 11 has zero open items:
Q1 fresh codebase, Q3 reviewer role (in-season route role still to pick when build
reaches routes), Q4 names, Q5 resolved via P33. Design is closed; build order starts.

### P35 — closed-wall registry (author: claude, prompted by khursani question, 2026-09-14)

Author concern: dead ends must be kept so agents never repeat the same work. Design already
keeps them (akar is append-only; LOSS verdicts, ceiling evidence, and closed axes all
persist), but persistence alone failed in kancil: closed-wall evidence existed on disk and
three agents still re-derived it. The failure is INJECTION, not storage. Proposal:

- Akar gains a derived, structured index `akar/closed_walls.jsonl`, maintained by harvest
  (writer: harvest): one row per dead end — {axis, why_closed, verdict, evidence_refs,
  season}. Rows are derived views of akar records, never hand-written.
- Injection rule: the closed-wall list is staged into EVERY agent's context at spawn,
  regardless of knowledge level — even `knowledge: none` agents receive it (none means
  no prior discoveries, never no warnings about closed work). Collab lane snapshots
  re-inject it each iteration.
- Evolution rule: a primary_change that targets an axis present in the closed-wall index
  must cite either new evidence since closure or an explicit reopen rationale; lint warns,
  the audit panel vetoes without one.
- Panel check: duplicate_discovery_rate above threshold is a rejection signal, fed by the
  registry.

Amends: sections 6 (harvest), 9 (staging), P14 (typed records). Status: proposed,
pending ratification.

### Session-2 amendments to P33/P34/P35 (source: codex critique, accepted 2026-09-14)

Source: proposals/codex-2026-09-14-s2.md (gpt-5.6-sol). Grounding note: the codex
sandbox could not read files (bwrap loopback error), so the critique ran on the
session-2 brief, which carries the mechanics; wording-level checks of this file
did not happen.

- P33: blinding plus one reconciliation round reduce answer copying, not
  correlation. Shared prompts, shared akar evidence, shared tools, and shared
  lineage still correlate reviewers. Proposed added invariants: quorum counts
  distinct failure domains (provider, model lineage, prompt lineage, evidence
  set), not family labels; the harness assigns reviewers only after artifacts are
  immutable; no ancestor, descendant, or recent reciprocal reviewer pairs; every
  sealed verdict is preserved after reconciliation; reconciliation appends a
  record, never replaces; abstentions do not count toward quorum; material
  dissent stays visible after the decision; a deterministic rule resolves
  unresolved disagreement; capture resistance via rotation, reciprocal-review
  limits, and unanimity-rate tracking with sampled operator audits; free stage
  means bounded execution with automatic demotion on integrity breaches, never
  irreversible or unaudited execution.
- P34: mutations need transactional semantics. Proposed invariants: a mutation
  names its base git tree SHA and a stale base is rejected; the harness applies
  all operations atomically with pre- and post-application lint; the graph stays
  acyclic with roots and terminals reachable; deleted nodes get tombstones; node
  ids stay stable across renames; every mutation records author, reviewers,
  citations, and rollback; rollback appends a ledger event and erases nothing.
  primary_change names the SEMANTIC change; supporting mechanical operations ride
  the same atomic patch, and the board must show them, because hidden supporting
  operations can carry the actual risk. Deletion needs protected node classes so
  removal cannot erase audit duties or evidence production.
- P35: a permanent registry can institutionalize a blind spot. Proposed:
  structured wall records (wall_id, closed claim, explicit exclusions, evidence
  content hashes, ratifying authority, creation season, review date, status in
  closed/review_due/reopened/superseded; records never removed); the harness
  flips closed to review_due on the review date and detects evidence-hash drift
  but cannot reopen semantically; reopening authority is stage-specific (manual:
  operator decides; panel: unrelated panel ratifies; free: panel within policy);
  injection is bounded summaries selected by deterministic scope, recorded as
  wall ids per execution event (start: 8 summaries or 2 KiB per node,
  configurable), not the full registry; closure authority is stronger than
  reopening because closing suppresses future search.

### P36 — operator board & season report (author: gpt-5.6-sol via codex session 2, recorded: claude, 2026-09-14)

Status: proposed. One harness-owned snapshot and event ledger; provenance labels
[H]/[A]/[D]; surfaces in priority order: status snapshot (JSON), `rumpun board`
(terminal snapshot, optional --watch TUI), self-contained static HTML season
report, deferred local read-only server. Full specification in section 13.
Decision points:

| # | Decision | Codex recommendation | Trade-off |
|---|---|---|---|
| D1 | live surface | board snapshot default, --watch optional | TUI adds terminal-compat work |
| D2 | between-season surface | static HTML report per season | duplicates derived presentation |
| D3 | local server | defer until schemas stabilize | loses live graph navigation for now |
| D4 | provenance | mandatory [H]/[A]/[D] labels | visual density |
| D5 | ledger protection | events outside agent-writable paths | install complexity; same-uid limit stated |
| D6 | alert delivery | incidents, exit codes, one disabled command hook fed by stdin event doc, never shell-interpolated agent text | hook expands exec surface |
| D7 | stall definition | durable harness-observed progress plus grace period | quiet legitimate work needs checkpoints or deadlines |
| D8 | panel transparency | sealed verdicts, correlation domains, reconciliation delta, surviving dissent | longer review |
| D9 | command grouping | season start/stop/status/show/report/list/direct; evolve plan/approve/apply/reject/rollback; runs into season list/show; prompt into season show --prompt | breaks top-level habits |
| D10 | closed-wall display | injected wall ids, omitted counts, review dates, reopening history | depends on recorded relevance selection |

Decision made: P36 ratified 2026-09-14, operator: "follow all default" — D1-D10
take the codex recommendations. Consequences: provenance labels [H]/[A]/[D] are
mandatory in every view; the harness event ledger lives outside agent-writable
paths; stall means durable harness-observed progress plus a grace period; board
is the live surface (snapshot default, --watch optional); a static HTML season
report lands with harvest; the local web server is deferred. Verb layout (D9):
top-level init, lint, graph, board, models, harvest; season
start/stop/status/list/show/report/direct; evolve plan/approve/apply/reject/
rollback; runs folds into season list/show; prompt folds into season show
--prompt. Harvest stays top-level: it remains an explicit operator action (the
codex condition for keeping it is met). The session-2 amendments to P33/P34/P35
above are accepted with the same answer.

### P37 — self-hosting: rumpun runs on itself (author: khursani directive, recorded: claude, 2026-09-14)

Status: ratified same day. Operator directive: "i want this library to use
itself to improve itself".

Decision made: this repo IS a rumpun project. `rumpun init` ran in the repo
root. rumpun.yaml carries the campaign goal "rumpun builds rumpun: ship the
ratified build order and close akar defects, one verified step per season"
(metric: verified_steps_per_season). Build-order steps become the campaign's
seasons; musim/s1.yaml targets build order step 3 (season start / board /
season stop) under the seed reference pipeline; lint and graph pass. akar/ is
seeded with the two standing findings (kancil-wall-injection,
codex-bwrap-sandbox), and routes are filled by `rumpun models --write`.

Bootstrap rule: until step 3 ships, seasons execute MANUALLY under the same
protocol — artifacts under rimba/sN/, akar records append-only, falsification
sealed before execution, verdicts at close. No quota-spending model calls
without the operator gate (P12/P9). The engine takes over the execute phase
the moment `season start` passes s1's own acceptance criteria; that event
closes s1, and evolve drafts s2 from real akar content.

The campaign goal locks at the first `season start` (goal_immutable). Before
that it is a normal edit.

P37 amendment (2026-09-14, operator request: make the supporter invisible to
the repo): all project state moved under `.rumpun/` per the section 4 layout.
Committed except `.rumpun/rimba/`. The difference from .omc-style caches is
recorded in section 4: caches are disposable and ignored; this directory is
the committed evidence ledger. The bootstrap files migrated with git mv;
lint and graph re-verified after the move.

## 14. Settlement run log (2026-09-14)

Operator order: run seasons continuously until the tool settles and is usable.

| season | outcome | ships |
|---|---|---|
| s3 | WIN 3/3, 851s | collab.py (flock lane module), tests/test_rumpun.py (15 green), first README, versions -> 0.4.0 |
| s4 | LOSS (band 1/3 on agent lane events) | report --serve on 127.0.0.1:8611 + state-sha footer (w3, surface 3), kill-marker fix landed from w1's blocker-report spec (harness-applied), +3 tests (18 green) |

s4 LOSS causes, both harness-observed: (1) season s4 w1's glm session spawned
with no file/exec tools -> wrote nothing, posted no lane events; w2 starved
waiting on w1's policy event; 15-minute stall rule fired (akar:
glm-toolless-spawn). (2) The lane protocol allowed a blocking wait on a peer
that could not write. GitHub issue draft for the tool-less spawn lives in the
akar record (hand over; owner khursani8 only).

P36 amendment, accepted under the operator's continuous-run order: surface 3
ships as `season report --serve` (rumpun-owned, loopback-only 127.0.0.1:8611,
renders first, prints the full URL, Ctrl-C exits 0) with a self-identifying
footer: project, season, state sha256[:12] [H].

Standing mitigations from this run:
- Every heredoc write of tracked state is read back in full before gate/spawn
  (two fabricated writes caught: akar harness-write-corruption).
- Lane protocol v2: no agent blocks on a peer event; defaults live in each
  prompt; lane events refine, never gate.
- Stall rule sized to the task: 20 min for full-file rewrites (s4's 15 min
  cut w3 mid-write).

### s5 (2026-09-14, later)

| season | outcome | ships |
|---|---|---|
| s5 | LOSS (lane band: w2 zero events) | engine state.lock (flock spans the whole spawn cycle; lost updates closed), `season list` verb, README --serve/list docs, v0.5.0 |

Tool-less spawn defect recurred on s5 w2: now 2 of 13 glm spawns. Protocol v2
did its job — w1 posted start/policy/done without blocking and delivered the
full lock design; the failure was contained to the agent that could not write.
The defect is external to this repo (spawned session tool inventory); akar
`glm-toolless-spawn` holds the issue draft. s6: dogfood attempt 3,
process-level dual-start test, `season show`.

### s6 (2026-09-14, later)

| season | outcome | ships |
|---|---|---|
| s6 | LOSS (show + README lost to tool-less spawns #3/#4) | process-level dual-start proof: two concurrent `season start` subprocesses serialize on state.lock, each benih spawned exactly once (suite 20/20) |

Tool-less spawn rate: 4 of 16. Mitigation shipped in the engine: spawned
children no longer inherit the model-suffix env vars (ANTHROPIC_MODEL,
ANTHROPIC_DEFAULT_*_MODEL) that resolve sessions to suffixed variants such as
glm-5.2[1m]; the relay maps suffixed sessions to a degraded toolset. One-spawn
diagnostic runs before the next season; if the defect persists, the remaining
verbs are harness-built under the s1 manual precedent instead of more retries.

### s7 (2026-09-14, later)

| season | outcome | ships |
|---|---|---|
| s7 | WIN (1 of 2 deliverables salvaged) | `rumpun direct` (P8: append/--list, pending vs consumed) + collab first-use fix + README at the v0.7.0 surface |

Salvage pattern, now used three times (s4 kill marker, s6 season show, s7
direct): a tool-less writer still reads the repo and drafts its full
implementation in agent.log; the harness applies it as targeted edits,
gates it, and smokes it. s7's smoke caught a real defect the untested patch
assumed away (append_event crashed on first use); collab.append_event now
tolerates a missing lane file (seq 0) and creates parent dirs. Tool-less
rate: 5 of 18 spawns. Remaining stubs: evolve approve/reject (s8),
evolve rollback (s9) — then the registry is empty and every designed verb
exists.

### s8 (2026-09-14, later)

| season | outcome | ships |
|---|---|---|
| s8 | WIN | `evolve approve` / `evolve reject` (ledger-backed, P33 on_reject recorded, drafts contained under musim/rejected/), +3 tests (24/24), two pre-existing defects fixed at merge: `python -m rumpun` now exits honestly (`__main__.py` swallows exit codes), and `cli.main` catches `akar.AkarError` (duplicate harvest exits 1, no traceback) |

w1 verified its own work via an overlay run before submitting (ruff, 21/21,
e2e exit codes) and flagged the two merge defects — the cleanest writer run
of the campaign. w2 was tool-less spawn #6 of 20; the harness applied the
test scope. Remaining stub: `evolve rollback` (s9), after which every
designed verb exists and the stub registry is empty.

### s9 (2026-09-14, later)

| season | outcome | ships |
|---|---|---|
| s9 | WIN | `evolve rollback` (contains applied seasons, records P33, never runs git), +7 tests (31/31), stub registry EMPTY |

Every designed verb now exists for the manual stage: init, lint, graph,
models, board, harvest, direct, season
start/stop/status/list/show/report(--serve), evolve plan/apply/approve/
reject/rollback. s9 also logged the first full two-way lane exchange
(6 events from both writers) and had zero tool-less spawns.
Open campaign question, with the operator: the pipeline DAG itself has never
mutated (analyze..falsify are declared but unexercised in engine seasons);
a reflection verb (`rumpun audit`) over the akar ledger is the proposed s11+
mechanism so structural changes happen only on cited evidence.

### s10 and campaign status (2026-09-14)

| season | outcome | ships |
|---|---|---|
| s10 | WIN | README truthful at v0.9.0: stub section removed, evolution loop documented; fresh-project quickstart dry run green (init, models --write, lint, list — no quota) |

**Campaign status: the ratified scope is closed.** Build order steps 1–5
shipped (init/scaffold, route probe, season engine, akar+harvest, evolve
draft/apply), P36 surfaces 0–3 shipped (status --json, board, static report,
report --serve on loopback 8611), every designed verb exists (stub registry
empty), 31 tests green, docs truthful, ten seasons on the ledger
(s1 manual; s2–s10: 6 WIN, 3 LOSS, all harvested honestly).

Known-open items, none blocking manual-stage use:
- Pipeline DAG never mutated; analyze..falsify declared but unexercised in
  engine seasons. Proposed mechanism (awaiting operator): `rumpun audit`
  reflection verb over the akar ledger — structural changes only on cited
  evidence.
- Tool-less spawn defect: 6 of 22 glm sessions; external, intermittent;
  akar record + issue draft; salvage pattern held every time.
- Codex bwrap sandbox broken on this box; codex routes untested end to end.
- fable route unprobed end to end (quota-gated).

## 15. Campaign phase 2 — self-evolution (operator order 2026-09-14)

The operator ordered the season chain to never stop: every season close
auto-seeds the next. Phase 1 (build the tool) is closed at s10. Phase 2 goal
(rumpun.yaml updated accordingly): rumpun evolves itself — each season,
reflection over the akar ledger generates candidate mutations of the
pipeline and parameters; every mutation carries cited evidence, a band, and
a rollback, and applies only through the existing gate (lint, operator at
manual stage). s11 builds the reflection verb (`rumpun audit`); its record
over s2–s10 is the first ledger-driven input to s12's season YAML.

### Dashboard v2 (2026-09-14, ui-ux-pro-max skill pass)

Report pages upgraded for progress-understanding, per the operator's request,
using the ui-ux-pro-max skill's design-system workflow (Dark OLED style,
density 8, chart + icon accessibility guidance):

- Campaign strip on every season page: one cell per season, colored and
  TEXT-labeled by verdict (never color alone), durations shown, links only to
  rendered reports (relative ../ links).
- Campaign tally line [D]: WIN/LOSS/NEUTRAL-INVALID/no-state counts.
- "Declared change this season" panel [A]: primary_change fields and evidence
  citations quoted verbatim from the season YAML.
- Duration bar chart [H]: inline SVG, per-season bars labeled with seconds
  and verdict; stat-style tally replaces charts under 4 data points.
- Dark OLED tokens (bg #020617, card #0E1223, border #334155, fg #F8FAFC,
  muted #94A3B8, WIN #22C55E, LOSS #EF4444, neutral #F59E0B, running
  #38BDF8), 4.5:1 contrast on text, visible focus, viewport meta.
- Deliberate deviations from the skill: no webfont import (self-contained,
  no external assets), no motion/animation (determinism; byte-identical
  renders re-verified), no JS (P36).
- Glyphs are inline SVG (Phosphor-style), aria-hidden, always beside visible
  text.

### Landing page (2026-09-14, operator feedback pass)

Operator verdict on dashboard v2: a progress-first reader still had to decode
a season page. Fix: rimba/index.html — the landing view rendered by
`rumpun audit`'s sibling, report.render_index. Opens with plain sentences:
campaign goal [A], "N seasons built · W WIN · L LOSS" [D], "Building right
now: <sid> — <goal line>" [A][H] (or Idle), "Last finished: <sid> <verdict>
in Ns — built: <goal>" [A][D], latest three results with goal lines verbatim,
then the strip and legend. Every season page now opens with a one-line plain
verdict: "WIN — built: <goal> — Ns" and an "all progress" link. Same
constraints held: no JS, no external assets, deterministic (byte-identical
re-render verified). Known transient: one unexplained single pytest failure
(30/31) during the render batch, not reproducible in three consecutive runs —
watch item, not a gate change.

### s11 and the first ledger-driven mutation (2026-09-14)

| season | outcome | ships |
|---|---|---|
| s11 | WIN | `rumpun audit [--last N]` — reflection over the ledger; audit-1 record: analyze/rank_gaps/hypothesize wrote artifacts in 0 of 8 engine seasons (plan/falsify named under the cap); 41/41 tests |

s12 executes the audit's candidates: the declared pipeline trims to
execute -> evaluate. The DAG forces the full head removal (plan reads
hypotheses.yaml, falsify reads experiments.yaml — their inputs vanish with
the head), so the 2-phase shape is the only lint-clean trim. This is the
first primary_change of type `remove` and the first season YAML whose scope
comes from the system's own reflection record instead of operator prose.

### s12 — the first pipeline mutation (2026-09-14)

| season | outcome | ships |
|---|---|---|
| s12 | LOSS (fresh-init condition unmet at close: w1 tool-less #7) | the lean 2-phase pipeline is now live in the season declaration AND the init scaffold (harness applied the audit-1-determined trim post-season, with a fresh-init lint proof); README documents the lean lifecycle |

The mutation audit-1 demanded is in effect: s12 ran and linted as
execute -> evaluate, every future draft inherits the shape, and fresh
projects scaffold it. The LOSS stands because the band judged the season's
own output, and its builder could not write. Tool-less rate: 7 of 24.

### s13 — reflection covers routes and bands (2026-09-14)

| season | outcome | ships |
|---|---|---|
| s13 | WIN (all four band conditions met) | audit.py extends run_audit: F4 per-route outcome tables (deliverable = any non-bookkeeping file, recursive; clean-empty is the tool-less signature), F5 LOSS-band masking flags, F6 budget-cap flag; 9 spec-first tests; suite 50/50 |

Live audit-2 on the real ledger (record sha256 0604ce19…): route glm is
13 clean-deliverable, 6 clean-empty, 0 failed, 0 not-exited over 19 spawns
(s5–s13); s5, s6, s12 flagged as LOSS seasons that shipped integrated
modules (bands masked value); campaign_cost_cap still unset (P9). Two
candidates armed: add a spawn tool-check for glm, recalibrate LOSS bands.
Integration notes: w1's audit.py landed verbatim; w2's tests needed two
harness reconciliations (budget key path is top-level budget.campaign_cost_cap
per scaffold.py; season verdicts read rimba verdicts.jsonl per report rule
[H]) and a dead-phase re-arming via a third declared phase so the priority
test does not unlink the audit's verdict source. First all-clean season:
zero tool-less spawns in s13.

### s14 — the detector season falsified its own premise (2026-09-14)

| season | outcome | ships |
|---|---|---|
| s14 | LOSS (stopped_stall at 900s; band unmet) | the calibration replay over all 31 recorded agent.logs FALSIFIED the text-signature premise: tp=7 fn=1 fp=21 tn=2; w2's additive-key safety tests landed (suite 54/54); the discovery record agentlog-no-tool-evidence replaces audit-2's tool-check candidate with a route rewire |

The season became its own evidence: w1 was tool-less boot #8 while building
the tool-less detector, and its log carries tool_use markers (ToolSearch
transcripts stream into agent.log), so marker families both under-detect and
over-detect. Clean logs carry zero markers because the CLI text output never
records tool events. The deterministic path is structured spawn output
(--output-format stream-json) — s15's cited candidate. Harness salvage: 2 of
w2's 14 tests landed (additive-key safety); the 12 classifier tests stay
unshipped, their subject falsified.

### s15 — route rewire proven, stall bug exposed (2026-09-14)

| season | outcome | ships |
|---|---|---|
| s15 | LOSS (stopped_stall at 900s; both writers killed by the stall bug) | the fable route + stream-json is proven live: first non-glm spawns, 6.3MB and 6.8MB event streams carrying Bash tool_use events; the engine stall rule measured runtime instead of progress and is hot-fixed (progress-based, regression test, suite 55/55, record stall-rule-fired-on-runtime) |

The irony is total: the tool-less detector season (s14) suffered a tool-less
boot, and the route-rewire season (s15) proved the rewire while being killed
by its own engine's stall rule. Both writers were mid-build, not stalled:
w1's log grew until 3 seconds before the kill. w1's stream also shows a new
writer-side failure mode — three successive nested-heredoc patch drafts, each
with corruption the writer caught and was repairing when killed. The parser
work moves to s16 with the two real streams as fixtures.

### s16 — the detector, landed (2026-09-14)

| season | outcome | ships |
|---|---|---|
| s16 | WIN (all five band clauses met) | engine parses spawn streams: per-snap file_tools from parsed tool events, offsets additive, ToolSearch-class never counts, finalize never guesses; 15 contract tests; suite 70/70; proven on the real s15 6.3MB/6.8MB streams |

The arc s14→s15→s16 is the loop working as designed: s14 falsified the
text-signature premise its own season was building, s15 proved the
structured-stream alternative live and exposed the stall bug, s16 landed
the parser seeded from the salvage of the season s15 killed. Two merge
reconciliations (offset always advances; marks land on the finalized snap)
are documented in the results rows. Campaign state: 9 WIN, 6 LOSS, one
NEUTRAL-era INVALID set, zero tool-less spawns since the route rewire.

### s17 — the budget rule fires; scope inherits (2026-09-14)

| season | outcome | ships |
|---|---|---|
| s17 | LOSS (stopped_budget at 1500s; zero clauses met) | evidence that the gate-hardening scope needs 40-minute budgets; a parse-clean H6 draft (akar serialization) and a 223-line spec-first test draft, both salvaged for s18 |

First stopped_budget in the campaign: the rule works. The s16 detector ran
live the whole season — per-snap file_tools true on both writers, offsets
advancing — and exposed its own first defect in production: the file-tool
warning fires per sighting instead of per transition, spamming the log.
s18: identical scope, 40-minute budgets, warning-transition fix added.

### s18 — the review's fix-first list, landed (2026-09-14)

| season | outcome | ships |
|---|---|---|
| s18 | WIN (all five band clauses met) | H1 finalize locking with under-lock liveness snapshots; H6 akar append serialization (s17 salvage adopted); H4 benih name containment; warning transition-only; all repro defects red-checked against unpatched code before merge; suite 84/84 |

Two seasons from review to landed fix (s17 budget LOSS, s18 WIN at the
retuned budget). The salvage loop worked twice: H6 from s17's killed draft,
tests from s17's killed pinning draft. Base staleness at merge (the copies
predated the mid-flight hook commit) was caught by the diff-before-land
discipline and reconciled. Next tier from the review: H2 terminate
identity, H3 spawn cwd, H7 citation hash checks.

### s19 — spawn and citation safety (2026-09-14)

| season | outcome | ships |
|---|---|---|
| s19 | WIN (all four band clauses met) | H2 identity-checked termination (recycled pid spared + warned, no dishonest marker); H3 enforced workspace cwd (all route shapes cwd-independent); H7 citation digest verification fail-closed (full or >=8-char prefix; missing sha256 refuses); 10 new pins; suite 94/94 |

Third straight evidence-cited merge from the external review's list. The
merge reconciliation discipline caught and hardened a racy pin: the
matched-identity test relied on shell trap timing (~1/5 red under load);
the contract is signaling-vs-sparing, so the pin now asserts death-vs-alive
directly and passes 8/8. Review backlog after s19: H5 startup cleanup, H8
rejected-season executability, H9 per-agent budgets, M-family items.

### s20 — the review's high list, complete (2026-09-14)

| season | outcome | ships |
|---|---|---|
| s20 | WIN (all four band clauses met) | H5 three-layer startup cleanup (validate-all pre-spawn, spawn-loop termination+error recording, spawn-intent persistence before Popen); H9 per-agent deadlines (terminated_budget mark, siblings untouched); H8 lifecycle enforcement (apply refuses rejected ids, start refuses non-canonical placement, rollback stops before recording); suite 99/100 with the recorded L2 flake |

The season itself hit the first TRUE stall under the fixed semantics: w1's
log froze 15 minutes and the rule stopped it correctly. The harness then
verified w1's scratch engine posthumously with its own 13-check repro
(all PASS) and completed the one unimplemented sub-clause w2's pin
specified (canonical-placement refusal, 5 lines). H1-H9 are now all
landed. Remaining: M-family findings, LOSS-band recalibration, cost cap.

### s21 — one verdict book, concrete routes, deterministic flake (2026-09-14)

| season | outcome | ships |
|---|---|---|
| s21 | WIN (all four band clauses met) | M3: harvest is the single verdict writer (season row lands in verdicts.jsonl, second harvest refused); M11: routes.py generates concrete, /bin/sh -n-validated commands (placeholder gone at the source); L2: the dual-start test demonstrates contention from outside and passed 5 consecutive loaded runs; suite 103/103 |

Process defect recorded: both writers edited the repository tree directly
instead of their workspaces (w1's own identity probe proves it); the
harness verified via git working-tree diff and the full gate rather than
copy-merge. w1 additionally caught three of its own write-corruption
incidents by readback (the known pattern) and drafted the evolved
dual-start issue for khursani8. Remaining knowns: M1 render determinism
for running seasons, M2 audit artifact set, M5-M9, LOSS-band
recalibration, cost cap.

### s22 — the core M-tier (2026-09-15)

| season | outcome | ships |
|---|---|---|
| s22 | WIN (all five band clauses met) | M1: every report view renders from persisted state only, links sorted, footer hash covers rendered bytes; M5: honest failed status + nonzero exits for rule-stopped and all-failed seasons; M6: reserved lane payload keys rejected; M7: shared-lock reads, single-write appends, partial-tail recovery; suite 108/108 |

Both writers held the workspace rule (the s21 violation did not recur).
One fixture reconciliation: the M5 pin's route killed its own wrapper
shell, which is a crash by honest semantics, not an agent failure — the
fixture now errors like an agent and the pin asserts the real scenario.
Remaining: M2 audit artifact set, M8 id reuse, M9 malformed input, M10
documented trade-off, LOSS-band recalibration, cost cap.

### s23 — reflection correctness (2026-09-15)

| season | outcome | ships |
|---|---|---|
| s23 | WIN (all five band clauses met) | M2: audit liveness judges each declared phase against its own writes file with an honest per-phase denominator; M8: draft ids from a lifecycle high-water mark (musim + rejected + akar records); M9: container guards in lint, non-string-key rejection recursing sequences, unhashable keys wrapped to YamlError; M10: mtime-only stall trade-off pinned at the code site and by test; suite 117/117 |

The M-family is complete (M1-M11). Two harness completions documented:
w2's yamlio recursion walked dicts only (nested sequences leaked a raw
TypeError), and its benih fixture left dangling continuation lines; both
finished to the pinned contracts. w2 shipped no notes (second occurrence)
- scratch artifacts carried the verification. The review that started at
s17 has now landed every finding tier: H1-H9, M1-M11, L2.

### s24 — backlog closure (2026-09-15)

| season | outcome | ships |
|---|---|---|
| s24 | WIN (all four band clauses met) | M10 candidate closed: stall progress is appended-byte growth (touch-only no longer defeats detection); harvest rows carry band/observed again via CLI flags; 6 pins; suite 123/123 |

The recorded backlog is empty. The two lanes' contracts diverged at merge
(watcher-memory history vs persisted scan stamps) and were reconciled so
both coexist: the scan stamps a content baseline plus growth-only progress
into workspace state, _agent_snap prefers stamps over history over mtime,
and the history-less callers keep the s15 estimate their pins require.
The external review (s17-s24) landed every finding; the loop now needs
new evidence sources - operator directives (rumpun direct) are the
standing invitation.

### s25 — the corpus gate (2026-09-15)

| season | outcome | ships |
|---|---|---|
| s25 | WIN (all four band clauses met) | tools/replay_corpus.py: discovers 53 scripts under akar evidence, executes the 6-script repro corpus against current main with per-script isolation, classifies honestly (6 PASS, 47 SKIP with reasons, 0 FAIL/DRIFT/REGRESSION); the matrix is a committed ledger artifact; the gate is itself pinned by the suite; 124/124 |

First season with zero merge friction. Both writers ran the corpus
independently and agreed on every verdict. The repro corpus is now a
maintained regression gate: any future change to main can be checked
against every ratified behavior since s17. audit-13 armed zero
candidates - with the review backlog and recorded candidates retired,
the loop's next evidence must come from new sources: the corpus matrix
itself, operator directives (rumpun direct), or the operator's cost cap.

### s26 — reflection reads its own regression gate (2026-09-15)

| season | outcome | ships |
|---|---|---|
| s26 | WIN (all four band clauses met) | run_audit ingests the newest corpus matrix: a FAIL/REGRESSION row arms a candidate placed first citing the script and first failing line, all-green yields a plain finding, absence changes nothing byte-for-byte; 5 pins; suite 129/129 |

Two consecutive zero-candidate audits (audit-13, audit-14) were the
evidence: reflection never read the one artifact that can show a
main-line regression. Now a regression announces itself to the loop.
One merge reconciliation: malformed matrix rows are skipped with one
DEBUG each (they are expected noise, not warnings) and unknown verdict
tokens get a fourth skip class. The refreshed matrix ran all green
(54 scripts discovered, 6 repro PASS). Review tiers complete, M-family
complete, backlog empty - the loop now maintains itself against its own
recorded behavior.

### s27 — the render loop becomes tooling (2026-09-15)

| season | outcome | ships |
|---|---|---|
| s27 | WIN (all four band clauses met) | tools/render_dashboard.py: renders every stateful season plus index and discoveries, skips stateless seasons with a logged reason, fails loudly on a missing campaign, and renders seasons in two passes so the first batch converges to the same bytes as every later run; 4 pins; suite 133/133 |

The per-close dashboard refresh no longer depends on a session-local
script. Two harness completions to the pinned contract: project-root
argument deriving .rumpun (matching every CLI verb), and two-pass season
rendering after w2 measured the strip-link ordering leak. w1 shipped no
notes (first w1 occurrence) - the tool and w2's pins carry the
verification. The M10 comment and this tool retire the last
session-ephemeral infrastructure.

## 16. The external-review arc and the corpus gate (s17-s27)

The campaign's first external reflection input: an independent codex review of
the 14 seasons of code to date (gpt-6-astra, bypass-sandbox route, 113,702
tokens; transcript in `akar/evidence/codex-review-2026-09-14/`). It returned
22 confirmed findings: 9 High, 11 Medium, 2 Low. Harness triage confirmed
every finding against source. The review's fix-first list (H1 finalize
locking, H4 workspace containment, H6 evidence append serialization) seeded
s17. Four seasons landed the high tier, two more the M-family, s24 closed
the backlog, and s25-s27 converted the record into standing infrastructure:
the corpus gate, the matrix-ingesting audit, and maintained render tooling.

| season | outcome | ships |
|---|---|---|
| s17 | LOSS (stopped_budget at 1500s; zero clauses met) | first stopped_budget of the campaign; the s16 detector ran live and exposed its warning-per-sighting defect; H6 draft and test draft salvaged for s18; budgets retuned to 40 minutes for the retake |
| s18 | WIN (all five band clauses met) | H1 finalize locking; H6 akar append serialization (s17 salvage adopted); H4 benih name containment; detector warning transition-only; suite 84/84; retuned budget validated |
| s19 | WIN (all four band clauses met) | H2 identity-checked termination; H3 enforced workspace cwd; H7 fail-closed citation digest checks; 10 pins; suite 94/94 |
| s20 | WIN (all four band clauses met) | H5 three-layer startup cleanup; H9 per-agent deadlines; H8 lifecycle enforcement; H1-H9 complete; the campaign's first TRUE stall (w1, verified posthumously via its own 13-check repro); suite 99/100 with the recorded L2 flake passing on re-run |
| s21 | WIN (all four band clauses met) | M3 single verdict writer; M11 concrete shell-validated routes; L2 barrier-fixed dual-start pin; suite 103/103; the arc's two workspace-rule violations recorded here (both writers edited the repository tree directly; harness verified via git working-tree diff plus the full gate) |
| s22 | WIN (all five band clauses met) | M1 deterministic persisted-state renders; M5 honest failed status and nonzero exits; M6 reserved lane payload keys rejected; M7 shared-lock reads and partial-tail recovery; suite 108/108; the workspace rule held |
| s23 | WIN (all five band clauses met) | M2 declared-artifact liveness with honest per-phase denominators; M8 season-id high-water mark; M9 input guards with sequence recursion; M10 trade-off pinned at code and test; M-family complete; suite 117/117 |
| s24 | WIN (all four band clauses met) | M10 candidate closed: stall progress is appended-byte growth (touch-only no longer defeats detection); harvest rows carry band/observed again; suite 123/123; recorded backlog empty |
| s25 | WIN (all four band clauses met) | `tools/replay_corpus.py`: 53 scripts discovered, the 6-script repro corpus run against current main (6 PASS, 47 SKIP, 0 FAIL/DRIFT/REGRESSION); the matrix committed as a ledger artifact; the gate pinned by the suite; suite 124/124; first zero-friction merge; audit-13 armed zero candidates |
| s26 | WIN (all four band clauses met) | `run_audit` ingests the newest corpus matrix: a FAIL/REGRESSION row arms a candidate placed first, all-green prints a plain finding, absence changes nothing byte-for-byte; suite 129/129; refreshed matrix: 54 scripts, 6 repro PASS |
| s27 | WIN (all four band clauses met) | `tools/render_dashboard.py`: renders every stateful season plus index and discoveries, skips stateless seasons with a logged reason, fails loudly on a missing campaign, two-pass rendering so the first batch converges to later-run bytes; suite 133/133; first production use at its own close |

Counts. Landed across s17-s24: H1-H9 (s18-s20), M1-M11 (s21-s23, the M10
candidate closed in s24), and L2 (s21): 21 of the review's 22 findings have a
recorded landing. L1 (discovery page links vs generated filenames) has no
recorded landing; checked against current main on 2026-09-15, the discovery
renderer still derives page hrefs from the raw record id while filenames use
the slugified id. L1 stays open rather than counted.

Process record. s17 fired the first stopped_budget (1500s) and forced the
budget retune; s18 reran the same scope at 40-minute budgets and met all five
band clauses. s21 recorded the arc's two workspace-rule violations: both
writers edited the repository tree directly instead of their workspaces; the
harness verified by git working-tree diff plus the full gate; no later season
repeated it. s20 ran the campaign's first TRUE stall (w1's log froze 15
minutes; the harness stopped it and verified the work posthumously through
its own 13-check repro). Harness completions to pinned contracts: s20
(canonical-placement refusal), s23 (yamlio sequence recursion, benih fixture
cleanup), s27 (project-root contract, two-pass rendering). Notes misses: w2
in s23 (second occurrence), w1 in s27 (first w1 occurrence).

Zero-candidate audits. audit-13 and audit-14 both returned "candidates:
none". The absence was the evidence: reflection never read the one artifact
that can show a main-line regression. s26 wired `run_audit` to ingest the
newest corpus matrix; audit-15 and audit-16 carry the corpus row (6 repro
scripts green on main, no candidates).

End state. The loop maintains itself against its labeled record: review
tiers complete except L1, M-family complete, backlog empty, the corpus gate
green on main, the audit matrix-aware, the render loop maintained tooling.
New evidence must come from the corpus matrix, operator directives, or the
operator's cost cap (still unset through audit-16).
