"""Pins for the evolution wave: issues #41 population, #42 selection, #43 memory."""

from __future__ import annotations

from rumpun import engine, harvest, lint

PROJ_YAML = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "cat {prompt} | true"
  judge: "cat {prompt} > /dev/null; cat ../../judge-answer.json"
"""

RACE_YAML = """\
id: s1
goal: "fixture"
metric: "m"
mode: race
methodology:
  approach: "x"
  evidence: []
  primary_change:
    type: add
    node: execute
    baseline: "b"
    expected_band: "WIN if x"
    rollback: "git revert"
    eval_window: "s1"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
      reads: results.jsonl
writers:
  - name: alpha
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 1}
  - name: beta
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 1}
stop:
  "on": [all_exited]
"""

FIGHT_YAML = RACE_YAML.replace("mode: race", "mode: fight").replace(
    "writers:", "writers:")


def _write_proj(tmp_path, proj_yaml=PROJ_YAML, season_text=RACE_YAML,
                judge_answer=None):
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    (root / "runs").mkdir()
    (root / "rumpun.yaml").write_text(proj_yaml, encoding="utf-8")
    (root / "prompts" / "dev").mkdir(parents=True, exist_ok=True)
    (root / "prompts" / "dev" / "dummy.md").write_text("body\n", encoding="utf-8")
    (root / "seasons" / "s1.yaml").write_text(season_text, encoding="utf-8")
    if judge_answer is not None:
        (root / "judge-answer.json").write_text(judge_answer, encoding="utf-8")
    return root


def test_lint_accepts_race_with_two_writers(tmp_path):
    root = _write_proj(tmp_path)
    findings = lint.lint(root / "seasons" / "s1.yaml")
    assert [f.message for f in findings if f.severity == "error"] == []


def test_lint_rejects_one_writer_race(tmp_path):
    beta = ("  - name: beta\n    route: glm\n"
            "    prompt: prompts/dev/dummy.md\n"
            "    knowledge: none\n    budget: {minutes: 1}\n")
    single = RACE_YAML.replace(beta, "")
    root = _write_proj(tmp_path, season_text=single)
    findings = lint.lint(root / "seasons" / "s1.yaml")
    assert any("two competing writers" in f.message
               for f in findings if f.severity == "error")


def test_race_close_adopts_all_and_harvests(tmp_path):
    root = _write_proj(
        tmp_path,
        judge_answer='{"adopt": ["alpha", "beta"], "reason": "both hold"}',
    )
    state = engine.start_season(root / "seasons" / "s1.yaml", root)
    assert state["status"] == "completed"
    assert state["judge"]["adopt"] == ["alpha", "beta"]
    path = harvest.harvest_season(root, "s1", "WIN", "raced")
    text = path.read_text(encoding="utf-8")
    assert "adopted: alpha, beta (both hold)" in text


def test_race_close_adopts_subset(tmp_path):
    root = _write_proj(
        tmp_path,
        judge_answer='{"adopt": ["alpha"], "reason": "beta diverged"}',
    )
    state = engine.start_season(root / "seasons" / "s1.yaml", root)
    assert state["status"] == "completed"
    assert state["judge"]["adopt"] == ["alpha"]
    path = harvest.harvest_season(root, "s1", "WIN", "raced")
    text = path.read_text(encoding="utf-8")
    assert "adopted: alpha (beta diverged)" in text
    assert "not adopted: beta" in text


def test_race_legacy_winner_still_harvests(tmp_path):
    root = _write_proj(tmp_path, judge_answer='{"winner": "alpha", "reason": "fast"}')
    state = engine.start_season(root / "seasons" / "s1.yaml", root)
    assert state["status"] == "completed"
    path = harvest.harvest_season(root, "s1", "WIN", "legacy judge")
    assert "adopted: alpha (fast)" in path.read_text(encoding="utf-8")


def test_race_adopt_none_fails_visible(tmp_path):
    root = _write_proj(
        tmp_path,
        judge_answer='{"adopt": [], "reason": "both broken"}',
    )
    state = engine.start_season(root / "seasons" / "s1.yaml", root)
    assert state["status"] == "failed"
    assert state["judge"]["adopt"] == []
    path = harvest.harvest_season(root, "s1", "NEUTRAL", "judge kept nothing")
    text = path.read_text(encoding="utf-8")
    assert "adopted: none (both broken)" in text


def test_race_judge_failure_fails_visible(tmp_path):
    root = _write_proj(tmp_path, judge_answer="not json at all")
    state = failure = None
    state = engine.start_season(root / "seasons" / "s1.yaml", root)
    failure = state.get("judge", {}).get("error")
    assert state["status"] == "failed"
    assert failure
    path = harvest.harvest_season(root, "s1", "NEUTRAL", "judge broke")
    text = path.read_text(encoding="utf-8")
    assert "adopted: none (judge returned no verdict)" in text


def test_lessons_compound_and_inject(tmp_path):
    root = _write_proj(
        tmp_path,
        season_text=FIGHT_YAML,
        judge_answer='{"winner": "alpha", "reason": "fast"}',
    )
    engine.start_season(root / "seasons" / "s1.yaml", root)
    harvest.harvest_season(root, "s1", "WIN", "lesson carries forward")
    lessons = root / "lessons.md"
    assert lessons.is_file()
    text = lessons.read_text(encoding="utf-8")
    assert "s1 WIN: lesson carries forward" in text
    # The next generation starts with the lesson injected into its prompt.
    (root / "seasons" / "s2.yaml").write_text(
        FIGHT_YAML.replace("id: s1", "id: s2"), encoding="utf-8",
    )
    engine.start_season(root / "seasons" / "s2.yaml", root)
    prompt = (root / "runs" / "s2" / "alpha" / "prompt.md").read_text(encoding="utf-8")
    assert "Campaign lessons" in prompt
    assert "lesson carries forward" in prompt
