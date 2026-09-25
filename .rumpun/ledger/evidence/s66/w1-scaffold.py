"""rumpun init — scaffold a project folder (build order step 1)."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("rumpun")

RUMPUN_DIR = ".rumpun"  # project state dir: committed ledger, hidden from ls


class ScaffoldError(Exception):
    pass


RUMPUN_YAML = """\
# rumpun.yaml — campaign-level config. Season-level config lives in seasons/s<N>.yaml.
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
      agent: judge
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
- `falsification.yaml` (sealed criteria).
- Your lane directive and knowledge staging from the ledger.

## Task
- Run your assigned experiments. Append discoveries to your discovery.md as you go.
- Fight mode: work independently. Collab mode: post leads to the lane (leads, not facts).

## Output contract
- Write `results.jsonl`: {experiment_id, outcome numbers, artifacts produced, minutes}.

## Constraints
- Do not read or reinterpret the falsification criteria; execute them as written.
""",
    "evaluate": """\
# Phase: evaluate (results vs committed falsification criteria)

## Inputs
- `falsification.yaml` (sealed), `results.jsonl`.

## Task
- Quote each committed criterion verbatim, then the result, then the verdict:
  kill | revise | retain | inconclusive (P16).
- Season verdict per writer: WIN | LOSS | NEUTRAL | INVALID, with an `implies` line.

## Output contract
- Write `verdicts.jsonl`: {experiment_id, criterion_verbatim, result, verdict, implies}.

## Constraints
- WIN below the declared noise floor is recorded as NEUTRAL with the reason (P1/P13).
- Every verdict cites on-disk evidence. An empty implies line is a defect, not a style.
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


def init_project(target: Path) -> None:
    if (target / RUMPUN_DIR / "rumpun.yaml").exists():
        msg = f"{target} already has .rumpun/rumpun.yaml — init refuses to overwrite"
        raise ScaffoldError(msg)
    _write(target / RUMPUN_DIR / "rumpun.yaml", RUMPUN_YAML)
    _write(target / RUMPUN_DIR / "seasons" / "s1.yaml", SEASON_S1)
    _write(target / RUMPUN_DIR / "seasons" / "_template.yaml", SEASON_TEMPLATE)
    for phase, content in PROMPTS.items():
        _write(target / RUMPUN_DIR / "prompts" / "base" / f"{phase}.md", content)
    _write(target / RUMPUN_DIR / "README.md", README)
    _write(target / RUMPUN_DIR / "adhd-rules.md", ADHD_RULES_CARD)
    for keep in (f"{RUMPUN_DIR}/ledger/.gitkeep",):
        _write(target / keep, "")
    _write(target / RUMPUN_DIR / "runs" / ".gitignore", "*\n!.gitignore\n")

    logger.info(ADHD_ACTIVATION_LINE)
