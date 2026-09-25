"""rumpun init — scaffold a project folder (build order step 1)."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger("rumpun")

RUMPUN_DIR = ".rumpun"  # project state dir: committed ledger, hidden from ls


class ScaffoldError(Exception):
    pass


RUMPUN_YAML = """\
# rumpun.yaml — campaign-level config. Season-level config lives in seasons/s<N>.yaml.
schema: 1             # campaign schema version; history in .rumpun/CHANGELOG.md
campaign:
  goal: ""            # FILL: verbatim campaign goal (immutable without human approval)
  metric: ""          # FILL: campaign metric
autonomy:             # P33 ratified 2026-09-14
  stage: manual       # manual | panel | free (promotion criteria below)
  promote_after: {clean_audits: 5}
  demote_on: {consecutive_rejects: 2}
  panel:
    families: [fable, glm, gpt-5.6-sol]
    rule: majority
    blinded: true
  invariants: [goal_immutable, budget_cap, falsify_required]   # panel cannot waive
  on_reject:
    action: rollback_to_last_good
    pause: true
    escalate_after: {consecutive_rejects: 2}
budget:
  campaign_cost_cap: null   # P9: set a number before 'rumpun start'
routes: {}                  # filled by 'rumpun models' (build order step 2)
"""

CHANGELOG_MD = """\
# CHANGELOG — campaign schema

One line per schema version, newest first. Readers refuse schema versions
outside the supported range (the rumpun.yaml `schema:` key) and point
here. The RESUME.md prune discipline applies: when a bump pushes the rows
past five, keep the five newest.

- schema 1: the initial campaign format (rumpun.yaml as shipped by `rumpun init`).
"""


SEASON_S1 = """\
# seasons/s1.yaml — the seed season. Fill goal/metric, then 'rumpun lint .rumpun/seasons/s1.yaml'.
id: s1
parent: null          # seed season: no primary_change required
goal: ""              # FILL
metric: ""            # FILL
mode: fight           # fight | collab
methodology:
  approach: "seed reference pipeline"
  evidence: []        # citations look like ledger:<record-id>@<sha> once the ledger has records
  pipeline:
    - phase: execute
      primitive: execute
      agents: writers
      prompt: prompts/base/execute.md
      writes: results.jsonl
    - phase: evaluate
      primitive: evaluate
      agents: writers
      prompt: prompts/base/evaluate.md
      reads: results.jsonl
      writes: verdicts.jsonl
writers:
  - name: a1
    route: glm-5.2     # resolved by route probe at spawn; placeholder until 'rumpun models'
    lane: base-approach
    prompt: prompts/base/execute.md
    knowledge: full
    budget: {minutes: 240}
  - name: a2
    route: fable
    lane: alt-approach
    prompt: prompts/base/execute.md
    knowledge: none
    budget: {minutes: 240}
stop:
  "on": [all_exited, {stall_minutes: 45}, budget_exhausted]
"""

SEASON_TEMPLATE = """\
# seasons/_template.yaml — shape of a NON-seed season (P12 fields shown).
# Everything above is identical to s1; the primary_change block is what lint enforces.
#
#   parent: s<N>
#   methodology:
#     approach: "..."
#     evidence: ["ledger:<record-id>@<sha>"]
#     primary_change:
#       type: add  # one of add,remove,rewire,retune or the bundle classes (P12)
#       node: <phase name>   # the one node this season's change is about (P12 Q1)
#       baseline: "parent best + how measured"
#       expected_band: "WIN if >= X, LOSS if <= Y"
#       rollback: "git revert to tag s<N> and re-run s<N> config"
#       eval_window: "which runs/artifacts decide the verdict"
id: sN
parent: null
goal: ""
metric: ""
mode: fight
methodology:
  approach: ""
  evidence: []
  pipeline: []
writers: []
stop:
  "on": [all_exited]
"""

COMPETITION_TEMPLATE = """\
# seasons/_competition.yaml — the competition season template (s67 w1).
# Shape of a Kaggle-competition season: baseline -> validate -> submit ->
# improve. The competition's own metric is the band; submission scores are
# the falsify gate. Copy to seasons/s<N>.yaml and fill every FILL field.
#
# Fill-in fields:
#   id                       — next free season id (s<N>, must match ^s\\d+$)
#   parent                   — season whose best stands as the baseline
#   goal                     — the competition goal, verbatim from its page
#   metric                   — the competition's official scoring metric
#   expected_band            — WIN/LOSS thresholds on the competition metric
#   writers[].route          — a route in rumpun.yaml (kancil needs the
#                              installed kancil CLI; 'rumpun models' probes)
#   writers[].budget.minutes — per-writer wall-clock budget
id: s68              # FILL: next free season id
parent: s67          # FILL: the season whose best stands as the baseline
goal: "drive the competition to a submission score that beats the sealed baseline"  # FILL
metric: "submission_scores"  # FILL: the competition's official metric
mode: fight
methodology:
  approach: "seal a baseline, pre-register the score gate, submit, improve"  # FILL: one line
  evidence: []       # FILL: citations look like ledger:<record-id>@<sha>
  primary_change:
    type: add
    node: baseline
    baseline: "the sealed baseline submission's competition-metric score"
    expected_band: "WIN if best submission >= baseline + <delta>; LOSS otherwise"  # FILL: <delta>
    rollback: "FILL: how this season's changes walk back to the parent best"
    eval_window: "the season's submissions.jsonl plus the competition leaderboard"
  pipeline:
    - phase: baseline
      primitive: execute
      agents: writers
      prompt: prompts/base/execute.md
      writes: baseline.jsonl
    - phase: validate
      primitive: falsify
      agents: writers
      prompt: prompts/base/falsify.md
      reads: baseline.jsonl
      writes: falsification.yaml
    - phase: submit
      primitive: execute
      agents: writers
      prompt: prompts/base/execute.md  # FILL: a kancil-ship submission prompt
      reads: falsification.yaml
      writes: submissions.jsonl
    - phase: improve
      primitive: hypothesize
      agents: writers
      prompt: prompts/base/hypothesize.md
      reads: submissions.jsonl
      writes: hypotheses.yaml
writers:
  - name: kancil-a        # FILL: per-season writer names
    route: kancil         # the installed kancil CLI (route in rumpun.yaml)
    lane: baseline-lane
    prompt: prompts/base/execute.md
    knowledge: full
    budget: {minutes: 240}
  - name: checker
    route: fable
    lane: alt-lane
    prompt: prompts/base/evaluate.md
    knowledge: none
    budget: {minutes: 240}
stop:
  "on": [all_exited, {stall_minutes: 45}, budget_exhausted]
"""

STEADY_STATE_TEMPLATE = """\
# seasons/_steady-state.yaml — the steady-state season template (s138 w2).
# The guide's section-4 steady state as a first-class shape: the standing
# light lanes (the lint sweep, the route probes, the rehearsals) keep the
# machinery warm while the operator holds the decision gate. Copy to
# seasons/s<N>.yaml and fill every FILL field before the first lint; the
# three lane briefs beside this template (the _steady-state-<lane>.md
# files) carry FILL slots for the campaign's standing guards, fill them too.
#
# Fill-in fields:
#   id                       — next free season id (s<N>, must match ^s\\d+$)
#   parent                   — the season whose close opened the steady state
#   goal / metric            — the steady state's own goal and metric words
#   approach                 — one line
#   evidence                 — citations look like ledger:<record-id>@<sha>
#   baseline                 — the standing surface the lanes re-prove
#   expected_band            — the operator's decision gate in the band:
#                              WIN/LOSS on the re-proof; anything heavier
#                              waits for the operator's word
#   rollback                 — how the season's changes walk back
#   eval_window              — which artifacts decide the verdict
#   writers[].name           — per-season writer names
#   writers[].route          — a route in rumpun.yaml ('rumpun models' probes)
#   writers[].budget.minutes — per-writer wall-clock budget
id: s1                   # FILL: next free season id
parent: s1               # FILL: the season whose close opened the steady state
goal: "keep the campaign machinery warm while the operator holds the decision gate"  # FILL
metric: "light-lane re-proofs"  # FILL: what a light lane re-proves
mode: fight              # the lanes run independently
methodology:
  approach: "re-prove the standing three (lint sweep, route probes, rehearsals)"  # FILL
  evidence: []           # FILL: citations look like ledger:<record-id>@<sha>
  primary_change:
    type: retune
    node: execute
    baseline: "the standing surfaces the last close left green"  # FILL: what the lanes re-prove
    expected_band: "operator's decision gate: WIN if lanes re-prove clean; LOSS on drift"  # FILL
    rollback: "nothing new ships; leaving the steady state is the operator's decision"  # FILL
    eval_window: "sweep.jsonl, probes.jsonl, rehearsals.jsonl, gate-report.jsonl"  # FILL
  pipeline:
    - phase: lint-sweep
      primitive: execute
      agents: writers
      prompt: seasons/_steady-state-lint-sweep.md
      writes: sweep.jsonl
    - phase: route-probes
      primitive: execute
      agents: writers
      prompt: seasons/_steady-state-route-probes.md
      writes: probes.jsonl
    - phase: rehearsals
      primitive: execute
      agents: writers
      prompt: seasons/_steady-state-rehearsals.md
      reads: [sweep.jsonl, probes.jsonl]
      writes: rehearsals.jsonl
    - phase: decision-gate
      primitive: evaluate
      agents: writers
      prompt: prompts/base/evaluate.md
      reads: rehearsals.jsonl
      writes: gate-report.jsonl
writers:
  - name: sweep      # FILL: per-season writer names
    route: glm-5.2   # resolved by route probe at spawn; placeholder until 'rumpun models'
    lane: lint-sweep
    prompt: seasons/_steady-state-lint-sweep.md
    knowledge: full
    budget: {minutes: 60}
  - name: probes
    route: fable
    lane: route-probes
    prompt: seasons/_steady-state-route-probes.md
    knowledge: none
    budget: {minutes: 30}
  - name: rehearsal
    route: glm-5.2
    lane: rehearsals
    prompt: seasons/_steady-state-rehearsals.md
    knowledge: partial
    budget: {minutes: 60}
stop:
  "on": [all_exited, {stall_minutes: 30}, budget_exhausted]
"""

STEADY_STATE_BRIEFS: dict[str, str] = {
    "lint-sweep": """\
# Lane: lint-sweep (the steady state's first light lane, s143 w1)

The campaign's standing lint guards already exist; this lane runs them
fresh and names any drift.

## Ground truth (fill at copy time)
- the guards: <FILL: the campaign's standing lint and doc guards>
- the template: seasons/_steady-state.yaml; this lane is its first phase
  and writes its first artifact

## Task
1. Run the standing guards fresh; re-prove each surface they cover.
2. Record the sweep in sweep.jsonl: one line per guard, with the name,
   the date, the outcome, and any drift found.
3. notes.md REQUIRED before ending the turn: what ran, the outcomes,
   and what remains. The close gate marks an exit without it incomplete.

## Bounds
- Writes: the season run dir only (sweep.jsonl, notes.md). Read-only on
  the campaign tree.
""",
    "route-probes": """\
# Lane: route-probes (the steady state's second light lane, s143 w1)

The campaign's spawn routes need a bounded probe each so the serve
table stays current.

## Ground truth (fill at copy time)
- the routes: <FILL: the routes to probe, from rumpun.yaml>
- the serve table: <FILL: where the campaign records which routes serve>
- the template: seasons/_steady-state.yaml; this lane is its second phase

## Task
1. Probe each route once, bounded: one call per route, no retries.
2. Confirm the serve table stands or name the drift.
3. Record the probes in probes.jsonl: one line per route, with the
   name, the date, served or not, and the latency if recorded.
4. notes.md REQUIRED before ending the turn: the probe outcomes and
   what remains. The close gate marks an exit without it incomplete.

## Bounds
- Writes: the season run dir only (probes.jsonl, notes.md). One bounded
  probe per route; no other network spend.
""",
    "rehearsals": """\
# Lane: rehearsals (the steady state's third light lane, s143 w1)

The rehearsal guards already exist: the exhaustion rehearsal, the guide walkthrough.
This lane runs them fresh and names any drift.

## Ground truth (fill at copy time)
- the guards: <FILL: the campaign's rehearsal guards>
- the template: seasons/_steady-state.yaml; this lane is its third
  phase and reads the sweep and the probes

## Task
1. Run the rehearsal guards fresh; confirm green or name the drift.
2. Record the reconfirmation in rehearsals.jsonl: one line per guard,
   with the name, the date, and the outcome.
3. notes.md REQUIRED before ending the turn: what ran, the outcomes,
   and what remains. The close gate marks an exit without it incomplete.

## Bounds
- Writes: the season run dir only (rehearsals.jsonl, notes.md).
  Read-only on the campaign tree.
""",
}

PROMPTS = {
    "analyze": """\
# Phase: analyze (error analysis on current best output)

## Inputs
- current best output + metric record (see season YAML `metric`)

## Task
- Enumerate concrete errors/gaps in the current best output. One error per line.
- For each: where it shows, evidence (file/line/metric delta), and a severity guess.

## Output contract
- Write `errors.jsonl`: one JSON object per error:
  {"id": "e1", "where": "...", "evidence": "...", "severity": "high|med|low"}

## Constraints
- Every claim cites something on disk. No invented numbers.
- Do not propose solutions here; that is the hypothesize phase.
""",
    "rank_gaps": """\
# Phase: rank_gaps (pick the top points worth resolving)

## Inputs
- `errors.jsonl` from analyze.

## Task
- Choose the top `top_n` gaps by expected metric impact over effort.
- Discard duplicates and cosmetic items explicitly (name what you dropped and why).

## Output contract
- Write `gaps.yaml`: list of {id, summary, source_error_ids, expected_impact, effort}.

## Constraints
- Do not invent new errors; rank what analyze produced.
""",
    "hypothesize": """\
# Phase: hypothesize (one hypothesis per gap)

## Inputs
- `gaps.yaml`.

## Task
- One hypothesis per gap: a falsifiable statement of cause and expected effect.
- State the mechanism, not just the correlation.

## Output contract
- Write `hypotheses.yaml`: {gap_id, hypothesis, mechanism, expected_direction}.

## Constraints
- A hypothesis the falsify phase cannot kill is not a hypothesis; sharpen it.
""",
    "plan": """\
# Phase: plan (experiment that tests each hypothesis)

## Inputs
- `hypotheses.yaml`.

## Task
- One experiment per hypothesis: what runs, on what data, measured how.
- Cheapest experiment that can kill the hypothesis first.

## Output contract
- Write `experiments.yaml`: {hypothesis_id, command/steps, data, metric_readout}.

## Constraints
- Experiments must run in this season's runs/ workspace. No network calls outside declared routes.
""",
    "falsify": """\
# Phase: falsify (pre-register the kill criterion BEFORE execution)

## Inputs
- `experiments.yaml`.

## Task
- For each experiment, write the kill criterion BEFORE results exist (P16, structured):
  comparator, metric, direction, threshold, dataset, confidence rule.
- State the consequence: kill | revise | retain | inconclusive.

## Output contract
- Write `falsification.yaml`: {experiment_id, metric, direction, threshold, dataset,
  confidence_rule, consequence}.

## Constraints
- This file is sealed (hashed) before execute starts. It cannot be edited after results.
- A criterion of the form "it works" is invalid; give a number and a direction.
""",
    "execute": """\
# Phase: execute (run the experiments as the season's writers)

## Inputs
- the season YAML `metric` and WIN/LOSS band (the sealed, lint-gated criteria).
- Your lane directive and knowledge staging from the ledger.

## Task
- Run your assigned experiments. Append discoveries to your discovery.md as you go.
- Fight mode: work independently. Collab mode: post leads to the lane (leads, not facts).

## Output contract
- Write `results.jsonl`: {experiment_id, outcome numbers, artifacts produced, minutes}.

## Constraints
- Do not read or reinterpret the falsification criteria; execute them as written.

## Exit contract
- Before you exit, write `notes.md` in the run dir: what was done, the
  evidence on disk, and what remains. The close gate marks an exit without
  it incomplete.
""",
    "evaluate": """\
# Phase: evaluate (results vs committed falsification criteria)

## Inputs
- `falsification.yaml` (sealed), `results.jsonl`.

## Task
- Quote each committed criterion verbatim, then the result, then the verdict:
  kill | revise | retain | inconclusive (P16).
- Season verdict per writer: WIN | LOSS | NEUTRAL | INVALID, with an `implies` line.
- Grade each LOSS clause of the season metric pass/fail.
- A met LOSS condition reads LOSS, verbatim in the verdict row.
- A WIN that met its band still reads WIN (no inversion).

## Output contract
- Write `verdicts.jsonl`: {experiment_id, criterion_verbatim, result, verdict, implies}.

## Constraints
- WIN below the declared noise floor is recorded as NEUTRAL with the reason (P1/P13).
- Every verdict cites on-disk evidence. An empty implies line is a defect, not a style.

## Exit contract
- Before you exit, write `notes.md` in the run dir: the verdicts and the
  evidence they cite, and what remains. The close gate marks an exit
  without it incomplete.
""",
}

README = """\
# rumpun project state (this directory: .rumpun/)

Everything the swarm needs lives here, out of the host repo's way:
- rumpun.yaml — campaign config: goal, autonomy stages, budget cap, routes.
- seasons/ — one YAML per season; s1 is the seed.
- ledger/ — append-only evidence ledger (committed).
- adhd-rules.md — the i-have-adhd output rules card (verbatim from github.com/ayghri/i-have-adhd).
- prompts/base/ — phase prompt templates; season overrides in prompts/sN/.
- runs/ — per-season workspaces (gitignored).

This directory is COMMITTED except runs/: git history over it is the
evolution ledger. Unlike .omc-style caches it is not disposable.

## First season
1. Fill campaign.goal and campaign.metric in rumpun.yaml.
2. Fill goal/metric in seasons/s1.yaml.
3. rumpun lint .rumpun/seasons/s1.yaml
4. rumpun graph .rumpun/seasons/s1.yaml
5. rumpun models — probe spawnable routes; --write fills rumpun.yaml.
6. rumpun season start — run the season (not yet implemented, build order step 3).
"""


ADHD_RULES_CARD = (
    "<!--\n"
    "i-have-adhd rules card. The rules below ship verbatim from\n"
    "https://github.com/ayghri/i-have-adhd (INSTALL.md, always-on block).\n"
    "-->\n"
    "\n"
    "## Output style\n"
    "\n"
    "The reader has ADHD. Shape every response so it can be acted on:\n"
    "\n"
    "1. Lead with the answer or next action: command, path, or snippet first.\n"
    "2. Number multi-step work; one bounded action per step.\n"
    "3. End with one next action doable in under two minutes.\n"
    "4. Finish the current issue before raising a new one.\n"
    '5. Restate progress each turn ("step 3 of 5 done").\n'
    '6. Give time estimates in concrete units, never "a bit".\n'
    "7. After a change, show what now works.\n"
    "8. Errors: state location, cause, and fix. No drama.\n"
    "9. Cap lists to 5 items.\n"
    "10. No preamble, no recaps, no closers.\n"
    "\n"
    "Exceptions: explain fully when asked to explain. Confirm before destructive"
    " actions. After three failed fixes, stop and name the doubtful assumption."
    " If the request is ambiguous, ask one short question.\n"
)

ADHD_ACTIVATION_LINE = (
    "activation: the i-have-adhd rules card is installed at .rumpun/adhd-rules.md;"
    " read it into your agent's persistent context (AGENTS.md/CLAUDE.md) or"
    ' type /i-have-adhd; rules stay on until "stop adhd mode"'
)


def _write(path: Path, content: str, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        msg = f"refusing to overwrite existing file: {path}"
        raise ScaffoldError(msg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info("wrote %s", path)


def _checker_source() -> Path:
    """The checker file of the source tree this installed rumpun came from.

    Issue #20: a scaffolded campaign had no tools/artifact_check.py, so its
    close refused 'checker not found'. The scaffold now ships the checker
    itself, copied from the source tree (walk-up from this module, the
    lint._load_design_checker convention) -- ruff-clean by construction.
    A source tree without the file is a structural refusal, never a
    silent skip.
    """
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        source = candidate / "tools" / "artifact_check.py"
        if source.is_file():
            return source
    msg = (
        f"no tools/artifact_check.py found above {here}: the scaffold "
        "ships the checker from the source tree (structural refusal)"
    )
    raise ScaffoldError(msg)


def init_project(target: Path) -> None:
    if (target / RUMPUN_DIR / "rumpun.yaml").exists():
        msg = f"{target} already has .rumpun/rumpun.yaml — init refuses to overwrite"
        raise ScaffoldError(msg)
    checker = _checker_source()  # resolve before any write lands
    _write(target / RUMPUN_DIR / "rumpun.yaml", RUMPUN_YAML)
    _write(target / RUMPUN_DIR / "CHANGELOG.md", CHANGELOG_MD)
    _write(target / RUMPUN_DIR / "seasons" / "s1.yaml", SEASON_S1)
    _write(target / RUMPUN_DIR / "seasons" / "_template.yaml", SEASON_TEMPLATE)
    _write(target / RUMPUN_DIR / "seasons" / "_competition.yaml", COMPETITION_TEMPLATE)
    _write(target / RUMPUN_DIR / "seasons" / "_steady-state.yaml", STEADY_STATE_TEMPLATE)
    for lane, brief in STEADY_STATE_BRIEFS.items():
        _write(
            target / RUMPUN_DIR / "seasons" / f"_steady-state-{lane}.md", brief
        )
    for phase, content in PROMPTS.items():
        _write(target / RUMPUN_DIR / "prompts" / "base" / f"{phase}.md", content)
    _write(target / RUMPUN_DIR / "README.md", README)
    _write(target / RUMPUN_DIR / "adhd-rules.md", ADHD_RULES_CARD)
    for keep in (f"{RUMPUN_DIR}/ledger/.gitkeep",):
        _write(target / keep, "")
    _write(target / RUMPUN_DIR / "runs" / ".gitignore", "*\n!.gitignore\n")

    dest = target / "tools" / "artifact_check.py"
    if dest.exists():
        msg = f"refusing to overwrite existing file: {dest}"
        raise ScaffoldError(msg)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(checker, dest)
    logger.info("shipped checker %s -> %s", checker, dest)

    logger.info(ADHD_ACTIVATION_LINE)


CHANGELOG_KEEP_ROWS = 5


def prune_changelog(dot: Path) -> Path:
    """Keep the CHANGELOG's newest CHANGELOG_KEEP_ROWS version rows.

    The RESUME.md prune discipline (rows older than the newest five drop)
    applied to schema history: when a schema bump pushes the rows past
    five, the older rows go. Atomic write; a missing file passes through.
    Returns the changelog path.
    """
    path = dot / "CHANGELOG.md"
    if not path.is_file():
        return path
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    rows = [i for i, line in enumerate(lines) if line.startswith("- schema ")]
    if len(rows) <= CHANGELOG_KEEP_ROWS:
        return path
    drop = set(rows[CHANGELOG_KEEP_ROWS:])
    kept = "".join(line for i, line in enumerate(lines) if i not in drop)
    tmp = path.with_suffix(".md.tmp")
    tmp.write_text(kept, encoding="utf-8")
    tmp.replace(path)
    return path
