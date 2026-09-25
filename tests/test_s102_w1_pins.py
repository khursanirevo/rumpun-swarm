"""s102 w1 pins — issue #19, the singular-agent evaluate phase.

Ground truth measured 2026-09-18 on current main (see the s102 w1 notes):
the engine staffs no pipeline phase; the spawn set is the writers table;
lint accepts any non-empty singular `agent`; the evaluate phase's declared
artifact (verdicts.jsonl) is written by the harvest close, harness-side,
in no season has a judge ever spawned. Fix surface chosen per the code's
shape: the scaffold emits the plural (`agents: writers`); the engine keeps
its single spawn source. Offline: stub routes, tmp_path, no network.

Red-first record: against the pre-fix tree the scaffold pin failed on the
emitted s1.yaml and _competition.yaml singular `agent:` keys; the two
engine-contract pins passed (they pin what the engine already does).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from rumpun import engine, harvest, lint, scaffold

RUMPUN_STUB = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  stub: "cat {prompt} > /dev/null"
"""

# The issue's literal season shape: execute staffed by the writers group,
# evaluate by a singular agent named judge. Prompt paths resolve to the
# fixture dummy prompt; the artifact contract mirrors the issue.
SEASON_ISSUE_19 = """\
id: s1
goal: "issue 19 repro"
metric: "m"
mode: fight
methodology:
  approach: "issue 19 repro"
  evidence: []
  pipeline:
    - phase: execute
      primitive: execute
      agents: writers
      prompt: prompts/dev/dumber.md
      writes: results.jsonl
    - phase: evaluate
      primitive: evaluate
      agent: judge
      prompt: prompts/dev/dumber.md
      reads: results.jsonl
      writes: verdicts.jsonl
writers:
  - name: a1
    route: stub
    lane: base-approach
    prompt: prompts/dev/dumber.md
    knowledge: full
    budget: {minutes: 1}
  - name: a2
    route: stub
    lane: alt-prompts
    prompt: prompts/dev/dumber.md
    knowledge: none
    budget: {minutes: 1}
stop:
  "on": [all_exited]
"""


def _write_issue_proj(tmp_path: Any, season_text: str) -> tuple[Path, Path]:
    """Build <tmp>/proj/.rumpun with the issue shape and a stub route."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    (root / "runs").mkdir()
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(RUMPUN_STUB, encoding="utf-8")
    (root / "prompts" / "dev" / "dumber.md").write_text("prompt body\n", encoding="utf-8")
    season = root / "seasons" / "s1.yaml"
    season.write_text(season_text, encoding="utf-8")
    return root, season


def test_s102w1_singular_agent_phase_spawns_no_judge(tmp_path: Any) -> None:
    """The engine contract the issue ran into: phases never staff spawns.

    A season yaml carrying the issue's literal singular-agent evaluate
    phase lints clean and starts; the spawn set is exactly the writers
    table and the evaluate node's declared artifact never appears at
    season end.
    """
    root, season = _write_issue_proj(tmp_path, SEASON_ISSUE_19)
    findings = lint.lint(season)
    errors = [f for f in findings if f.severity == "error"]
    assert not errors, [f.message for f in errors]
    state = engine.start_season(season, root)
    assert state["status"] == "completed"
    assert sorted(state["spawned"]) == ["a1", "a2"]
    agent_dirs = sorted(
        p.name for p in (root / "runs" / "s1").iterdir() if p.is_dir()
    )
    assert agent_dirs == ["_season", "a1", "a2"]
    assert not (root / "runs" / "s1" / "verdicts.jsonl").exists(), (
        "the evaluate phase's declared artifact appeared without a spawned judge"
    )


def test_s102w1_scaffold_emits_only_writer_group_references(tmp_path: Any) -> None:
    """Every emitted pipeline node references a group the engine can staff.

    The engine spawns the writers table only, so every emitted phase node
    must carry `agents` in WRITER_KEYS and none may carry the singular
    `agent:` key (the fiction that produced issue #19).
    """
    target = tmp_path / "proj"
    scaffold.init_project(target)
    seasons = target / ".rumpun" / "seasons"
    for name in ("s1.yaml", "_template.yaml", "_competition.yaml"):
        doc = yaml.safe_load((seasons / name).read_text(encoding="utf-8"))
        nodes = (doc.get("methodology") or {}).get("pipeline") or []
        for node in nodes:
            assert "agent" not in node, (
                f"{name} node '{node.get('phase')}': singular agent key emitted"
            )
            assert node.get("agents") in lint.WRITER_KEYS, (
                f"{name} node '{node.get('phase')}': unspawnable group "
                f"{node.get('agents')!r}"
            )


def test_s102w1_harvest_close_writes_the_evaluate_artifact(tmp_path: Any) -> None:
    """The divergence explained as a pin: the close, not a judge, writes it.

    A scaffolded season runs to completed with no verdicts.jsonl; the
    harvest close then writes the evaluate phase's declared artifact
    harness-side while the workspace still holds exactly the two writer
    dirs. This is how audit-45's F1 counted artifact liveness 9 of 9
    without a judge ever spawning.
    """
    target = tmp_path / "proj"
    scaffold.init_project(target)
    root = target / ".rumpun"
    s1 = root / "seasons" / "s1.yaml"
    s1.write_text(
        s1.read_text(encoding="utf-8")
        .replace('goal: ""', 'goal: "issue 19"')
        .replace('metric: ""', 'metric: "m"'),
        encoding="utf-8",
    )
    ry = root / "rumpun.yaml"
    ry.write_text(
        ry.read_text(encoding="utf-8").replace(
            "routes: {}",
            'routes:\n'
            '  glm-5.2: "cat {prompt} > pin"\n'
            '  fable: "cat {prompt} > pin"',
        ),
        encoding="utf-8",
    )
    state = engine.start_season(s1, root)
    assert state["status"] == "completed"
    assert not (root / "runs" / "s1" / "verdicts.jsonl").exists()
    harvest.harvest_season(root, "s1", verdict="NEUTRAL", implies="the close wrote it")
    row = json.loads(
        (root / "runs" / "s1" / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert row["season"] == "s1"
    agent_dirs = sorted(p.name for p in (root / "runs" / "s1").iterdir() if p.is_dir())
    assert agent_dirs == ["_season", "a1", "a2"]
