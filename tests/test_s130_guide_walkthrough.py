"""s130 w2: the campaign guide's happy path, walked end to end in tmp.

One module-scoped walk builds a fresh consumer campaign in pytest's tmp
(tmp only; the real campaign is never touched) and drives every step the
guide names, capturing each command's rc and output: init, models --write,
the fills, graph, lint, a minimal season start to completed, the close
(design row, design lint, harvest, the close commit, check, push), and the
keep-going loop (audit, evolve plan/apply/approve, loop --once, direct,
resume, kanban). The writers run a hand-tuned stub route, the cheapest
honest season the scaffold allows: the walk proves the PATH, not writer
quality.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[1]

WALK_ROUTE = (
    "  walk: \"printf 'walk lane shipped' > notes.md"
    " && printf 'walk deliverable' > deliverable.md\"\n"
)

DESIGN_ROW = (
    "| s1 | WIN | runs/s1/a1/deliverable.md: the walk lane shipped; "
    "runs/s1/a2/deliverable.md: the alt lane shipped |\n"
)

ASSESSMENT = """\
verdict: "CONTINUE"
basis: "why the campaign continues, citing ledger records"
fronts:
- name: "the one open front"
  owner: "campaign"
  basis: "what is open, with the record id that names it"
  next: "the next action"
satisfied:
- "what landed since the last seal, with record ids"
"""

REQUIRED_RC0 = (
    "init",
    "models_write",
    "graph",
    "lint",
    "season_start",
    "season_status",
    "season_list",
    "season_show",
    "season_report",
    "design_lint",
    "harvest",
    "check_close",
    "push",
    "audit",
    "evolve_plan",
    "evolve_apply",
    "evolve_approve",
    "loop_once",
    "direct",
    "direct_list",
    "resume",
    "kanban",
    "plugin_list",
)


def _rumpun(step: str, argv: list[str], results: dict[str, Any]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "rumpun", *argv],
        cwd=results["proj"], env=results["env"], capture_output=True,
        text=True, timeout=300, check=False,
    )
    results["steps"][step] = {
        "rc": proc.returncode,
        "out": proc.stdout,
        "err": proc.stderr,
    }
    return results["steps"][step]


def _git(step: str, argv: list[str], results: dict[str, Any]) -> dict[str, Any]:
    proc = subprocess.run(
        ["git", *argv],
        cwd=results["proj"], env=results["git_env"], capture_output=True,
        text=True, timeout=60, check=False,
    )
    results["steps"][step] = {
        "rc": proc.returncode,
        "out": proc.stdout,
        "err": proc.stderr,
    }
    return results["steps"][step]


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{path}: fill anchor missing: {old!r}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _harvest_argv(extra: list[str]) -> list[str]:
    return [
        "harvest", "s1", "--verdict", "WIN",
        "--implies", "the seed pipeline ran end to end",
        "--band", "WIN if the pipeline completes, LOSS if any writer ships nothing",
        "--observed", "completed, 2 writers, 0 stall",
        *extra,
    ]


def _walk(tmp_dir: Path) -> dict[str, Any]:
    proj = tmp_dir / "proj"
    proj.mkdir()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src")
    git_env = dict(env)
    for key in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
                "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
        git_env[key] = "walk"
    git_env["GIT_AUTHOR_EMAIL"] = "walk@local"
    git_env["GIT_COMMITTER_EMAIL"] = "walk@local"
    results: dict[str, Any] = {
        "proj": proj, "env": env, "git_env": git_env, "steps": {},
    }

    # --- section 1: init, models, the fills, graph, lint
    _rumpun("init", ["init"], results)
    _rumpun("init_again", ["init"], results)  # the guide's refusal: rc 1
    _rumpun("models_write", ["models", "--write"], results)

    dot = proj / ".rumpun"
    _replace(
        dot / "rumpun.yaml",
        '  goal: ""',
        '  goal: "prove the campaign guide\'s happy path end to end"',
    )
    _replace(
        dot / "rumpun.yaml",
        '  metric: ""',
        '  metric: "every walk step rc 0"',
    )
    _replace(dot / "rumpun.yaml", "  campaign_cost_cap: null",
             "  campaign_cost_cap: 1")
    routes_text = (dot / "rumpun.yaml").read_text(encoding="utf-8")
    assert "\nwalk:" not in routes_text
    assert "routes: {}" not in routes_text  # models --write filled the block
    assert "routes:" in routes_text
    lines = routes_text.splitlines(keepends=True)
    at = next(i for i, ln in enumerate(lines) if ln.startswith("routes:"))
    lines.insert(at + 1, WALK_ROUTE)
    (dot / "rumpun.yaml").write_text("".join(lines), encoding="utf-8")

    s1 = dot / "seasons" / "s1.yaml"
    _replace(s1, 'goal: ""', 'goal: "prove the guide\'s happy path end to end"')
    _replace(s1, 'metric: ""', 'metric: "every walk step rc 0"')
    _replace(s1, "route: glm-5.2", "route: walk")
    _replace(s1, "route: fable", "route: walk")
    _replace(s1, "budget: {minutes: 240}", "budget: {minutes: 1}")

    _git("git_init", ["init", "-q", "-b", "main"], results)
    _git("git_commit_scaffold",
         ["add", ".rumpun/rumpun.yaml", ".rumpun/CHANGELOG.md",
          ".rumpun/seasons", ".rumpun/prompts", ".rumpun/ledger",
          ".rumpun/README.md", ".rumpun/adhd-rules.md",
          "tools/artifact_check.py"],
         results)
    _git("git_commit_scaffold",
         ["commit", "-q", "-m", "chore: scaffold the walk campaign",
          "--", ".rumpun/rumpun.yaml", ".rumpun/CHANGELOG.md",
          ".rumpun/seasons", ".rumpun/prompts", ".rumpun/ledger",
          ".rumpun/README.md", ".rumpun/adhd-rules.md",
          "tools/artifact_check.py"],
         results)
    origin = tmp_dir / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)],
                   check=True)
    results["origin"] = origin
    _git("push", ["remote", "add", "origin", str(origin)], results)

    _rumpun("graph", ["graph", ".rumpun/seasons/s1.yaml"], results)
    _rumpun("lint", ["lint", ".rumpun/seasons/s1.yaml"], results)

    # --- section 2: the season, start to completed
    spine = _rumpun("season_start", ["season", "start", ".rumpun/seasons/s1.yaml"],
                    results)
    assert spine["rc"] == 0, f"season start failed: {spine['err'][-2000:]}"
    _rumpun("season_status", ["season", "status", "s1"], results)
    _rumpun("season_list", ["season", "list"], results)
    _rumpun("season_show", ["season", "show", "s1"], results)
    _rumpun("season_report", ["season", "report", "s1"], results)

    # --- section 3: the close (design row, lint, harvest, commit, check, push)
    (proj / "DESIGN.md").write_text(
        "# DESIGN — campaign design rows\n\n"
        "| season | verdict | ships (one line) |\n"
        "|---|---|---|\n" + DESIGN_ROW,
        encoding="utf-8",
    )
    (proj / "assessment-s1.yaml").write_text(ASSESSMENT, encoding="utf-8")
    gate = _rumpun("design_lint", ["lint", "DESIGN.md"], results)
    assert gate["rc"] == 0, f"design lint failed: {gate['err'][-2000:]}"
    close = _rumpun("harvest", _harvest_argv(["--assessment-file",
                                              "assessment-s1.yaml"]), results)
    assert close["rc"] == 0, f"harvest failed: {close['err'][-2000:]}"
    _rumpun("harvest_again", _harvest_argv([]), results)  # refusal: rc 1

    _git("close_commit",
         ["add", "DESIGN.md", "assessment-s1.yaml", ".rumpun/rumpun.yaml",
          ".rumpun/CHANGELOG.md", ".rumpun/seasons", ".rumpun/prompts",
          ".rumpun/ledger", ".rumpun/README.md", ".rumpun/adhd-rules.md"],
         results)
    _git("close_commit",
         ["commit", "-q", "-m", "feat: s1 closes the seed season", "--",
          "DESIGN.md", "assessment-s1.yaml", ".rumpun/rumpun.yaml",
          ".rumpun/CHANGELOG.md", ".rumpun/seasons", ".rumpun/prompts",
          ".rumpun/ledger", ".rumpun/README.md", ".rumpun/adhd-rules.md"],
         results)
    _rumpun("check_close", ["check", "s1", "HEAD"], results)
    _git("push", ["push", "-q", "-u", "origin", "main"], results)

    # --- section 4: keep going
    _rumpun("audit", ["audit", "--last", "3"], results)
    _rumpun("evolve_plan", ["evolve", "plan", ".rumpun/seasons/s1.yaml"], results)
    harvest_record = sorted((dot / "ledger").glob("*_s1-harvest.md"))[0]
    seal = next(ln.split("sha256: ", 1)[1].strip()
                for ln in harvest_record.read_text(encoding="utf-8").splitlines()
                if ln.startswith("sha256: "))
    s2 = dot / "seasons" / "s2.yaml"
    draft = s2.read_text(encoding="utf-8")
    assert "  evidence: []" in draft, f"no evidence anchor in the draft: {draft[:500]}"
    assert '    baseline: ""' in draft, (
        f"no primary_change skeleton in the draft: {draft[:800]}"
    )
    draft = draft.replace(
        "  evidence: []",
        '  evidence: ["ledger:s1-harvest@' + seal[:8] + '"]',
        1,
    )
    for empty, filled in (
        ('    baseline: ""',
         '    baseline: "s1 completed: both lanes shipped their notes.md"'),
        ('    expected_band: ""',
         '    expected_band: "WIN if s2 completes, LOSS if any writer fails"'),
        ('    rollback: ""',
         '    rollback: "restore the s1 season yaml and re-run it"'),
        ('    eval_window: ""',
         '    eval_window: "the s2 run and its results.jsonl"'),
    ):
        assert empty in draft, f"draft anchor missing: {empty!r}"
        draft = draft.replace(empty, filled, 1)
    s2.write_text(draft, encoding="utf-8")
    _rumpun("evolve_apply", ["evolve", "apply", ".rumpun/seasons/s2.yaml"], results)
    _rumpun("evolve_approve", ["evolve", "approve", ".rumpun/seasons/s2.yaml"],
            results)
    _rumpun("loop_once", ["loop", "--once"], results)
    _rumpun("direct", ["direct", "walk the guide again after the next merge"],
            results)
    _rumpun("direct_list", ["direct", "--list"], results)
    _rumpun("resume", ["resume"], results)
    _rumpun("kanban", ["kanban"], results)
    _rumpun("plugin_list", ["plugin", "list"], results)

    results["state"] = json.loads(
        (dot / "runs" / "s1" / "_season" / "state.json").read_text(encoding="utf-8")
    )
    results["results_rows"] = [
        json.loads(ln)
        for ln in (dot / "runs" / "s1" / "results.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if ln.strip()
    ]
    results["ledger_ids"] = set()
    for path in (dot / "ledger").iterdir():
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("id: "):
                    results["ledger_ids"].add(line[4:].strip())
    results["verdicts"] = [
        json.loads(ln)
        for ln in (dot / "runs" / "s1" / "verdicts.jsonl")
        .read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    processed = dot / "events" / ".processed"
    results["processed"] = (
        processed.read_text(encoding="utf-8").split() if processed.is_file() else []
    )
    results["check_records"] = [
        p.name for p in (dot / "ledger").iterdir() if "check-s1" in p.name
    ]
    return results


@pytest.fixture(scope="module")
def walk_results(tmp_path_factory) -> dict[str, Any]:
    return _walk(tmp_path_factory.mktemp("s130_guide_walk"))


def test_walk_required_steps_exit_zero(walk_results: dict[str, Any]) -> None:
    for step in REQUIRED_RC0:
        entry = walk_results["steps"].get(step)
        assert entry is not None, f"step never ran: {step}"
        assert entry["rc"] == 0, f"{step}: rc {entry['rc']}\n{entry['err'][-2000:]}"


def test_walk_init_refusal_and_second_harvest_refusal(
    walk_results: dict[str, Any],
) -> None:
    assert walk_results["steps"]["init_again"]["rc"] == 1
    assert "refuses to overwrite" in walk_results["steps"]["init_again"]["err"]
    assert walk_results["steps"]["harvest_again"]["rc"] == 1
    assert "refusing second harvest" in walk_results["steps"]["harvest_again"]["err"]


def test_walk_scaffold_matches_the_guide_table(
    walk_results: dict[str, Any],
) -> None:
    dot = walk_results["proj"] / ".rumpun"
    for rel in ("rumpun.yaml", "CHANGELOG.md", "seasons/s1.yaml",
                "seasons/_template.yaml", "seasons/_competition.yaml",
                "ledger", "runs", "README.md", "adhd-rules.md"):
        assert (dot / rel).exists(), f"scaffold missing {rel}"
    prompts = sorted(p.stem for p in (dot / "prompts" / "base").iterdir())
    assert prompts == ["analyze", "evaluate", "execute", "falsify",
                       "hypothesize", "plan", "rank_gaps"]
    assert (walk_results["proj"] / "tools" / "artifact_check.py").is_file()


def test_walk_season_completed_with_notes_and_results(
    walk_results: dict[str, Any],
) -> None:
    state = walk_results["state"]
    assert state["status"] == "completed"
    assert "completed" in walk_results["steps"]["season_status"]["out"]
    for name in ("a1", "a2"):
        agent = state["agents"][name]
        assert agent["state"] == "exited"
        assert agent["exit_code"] == 0
        assert "incomplete" not in agent
        ws = walk_results["proj"] / ".rumpun" / "runs" / "s1" / name
        assert (ws / "notes.md").is_file()
        assert (ws / "deliverable.md").is_file()
    rows = {r["unit"]: r for r in walk_results["results_rows"]}
    assert sorted(rows) == ["a1", "a2"]
    for row in rows.values():
        assert row["state"] == "exited"
        assert row["exit_code"] == 0
        assert "incomplete" not in row


def test_walk_close_records_land(walk_results: dict[str, Any]) -> None:
    ids = walk_results["ledger_ids"]
    assert "s1-harvest" in ids
    assert "usefulness-s1" in ids
    assert "approve-s2" in ids
    (row,) = walk_results["verdicts"]
    assert row["verdict"] == "WIN"
    assert row["implies"] == "the seed pipeline ran end to end"
    assert "salvaged" not in row
    lessons = (walk_results["proj"] / ".rumpun" / "lessons.md").read_text(
        encoding="utf-8"
    )
    assert "- s1 WIN: the seed pipeline ran end to end" in lessons


def test_walk_check_takes_the_pinless_named_skip(
    walk_results: dict[str, Any],
) -> None:
    """The drift pin: the guide's close says the checker appends the
    check-s1 record; a pinless consumer close takes the s108 named skip
    instead -- exit 0, no record. The guide fix names the skip."""
    step = walk_results["steps"]["check_close"]
    assert step["rc"] == 0
    assert "no pins lane" in step["err"]
    assert walk_results["check_records"] == []


def test_walk_push_landed_on_origin(walk_results: dict[str, Any]) -> None:
    assert walk_results["steps"]["push"]["rc"] == 0
    head = subprocess.run(
        ["git", "-C", str(walk_results["proj"]), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    origin = subprocess.run(
        ["git", "-C", str(walk_results["origin"]), "rev-parse", "main"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert origin == head


def test_walk_loop_drained_both_events(walk_results: dict[str, Any]) -> None:
    processed = walk_results["processed"]
    assert "season-completed-s1.json" in processed
    assert "season-harvested-s1.json" in processed
    assert walk_results["steps"]["evolve_apply"]["rc"] == 0
    assert (walk_results["proj"] / ".rumpun" / "seasons" / "s2.yaml").is_file()
