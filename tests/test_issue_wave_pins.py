"""Pins for the issues wave: khursanirevo/rumpun #18 #25 #26 #27 #28 #29 #30."""

from __future__ import annotations

import fcntl
import importlib.util
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

from rumpun import akar, cli, harvest, lint, loop, scaffold

CHECKER = Path(__file__).resolve().parents[1] / "tools" / "artifact_check.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("artifact_check", CHECKER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["artifact_check"] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_proj(tmp_path):
    """A campaign state dir with two seasons, s1 older than s2."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    (root / "runs").mkdir()
    (root / "rumpun.yaml").write_text(
        "autonomy:\n"
        "  stage: manual\n"
        "  invariants: [goal_immutable, budget_cap, falsify_required]\n"
        "routes:\n"
        '  glm: "cat {prompt} | true"\n',
        encoding="utf-8",
    )
    for sid in ("s1", "s2"):
        (root / "seasons" / f"{sid}.yaml").write_text(
            f'id: {sid}\ngoal: "fixture {sid}"\nmetric: "m"\n', encoding="utf-8"
        )
    return root


def _season_state(root, sid, status="completed", agents=None):
    state_dir = root / "runs" / sid / "_season"
    state_dir.mkdir(parents=True, exist_ok=True)
    if agents is None:
        agents = {
            "w1": {
                "name": "w1",
                "route": "glm",
                "state": "exited",
                "exit_code": 0,
                "seconds": 1.0,
            }
        }
    (state_dir / "state.json").write_text(
        json.dumps(
            {
                "id": sid,
                "status": status,
                "started_at": 1.0,
                "ended_at": 1545.0,
                "agents": agents,
            }
        ),
        encoding="utf-8",
    )


# --- #18 spend line -----------------------------------------------------------


def test_spend_line_shape(tmp_path):
    root = _write_proj(tmp_path)
    _season_state(
        root,
        "s1",
        agents={
            "w1": {"name": "w1", "route": "glm", "state": "exited",
                   "exit_code": 0, "seconds": 1.0},
            "w2": {"name": "w2", "route": "glm", "state": "exited",
                   "exit_code": 0, "seconds": 3086.0},
        },
    )
    path = harvest.harvest_season(root, "s1", "WIN", "note")
    text = path.read_text(encoding="utf-8")
    assert "spend: writers=2 writer_seconds=3087.0 duration_s=1544" in text
    assert "tokens" not in text and "api cost" not in text


def test_spend_line_ignores_non_numeric_seconds(tmp_path):
    root = _write_proj(tmp_path)
    _season_state(
        root,
        "s1",
        agents={
            "w1": {"name": "w1", "route": "glm", "state": "exited",
                   "exit_code": 0, "seconds": 1.0},
            "w2": {"name": "w2", "route": "glm", "state": "exited",
                   "exit_code": 0, "seconds": "still running"},
        },
    )
    path = harvest.harvest_season(root, "s1", "WIN", "note")
    text = path.read_text(encoding="utf-8")
    assert "spend: writers=2 writer_seconds=1.0 duration_s=1544" in text


# --- #26 season list order ----------------------------------------------------


def test_season_list_newest_first(tmp_path, capsys, monkeypatch):
    root = _write_proj(tmp_path)
    monkeypatch.chdir(root.parent)
    args = cli.build_parser().parse_args(["season", "list"])
    args.func(args)
    out = capsys.readouterr().out
    assert out.index("s2") < out.index("s1")


# --- #25 execute prompt -------------------------------------------------------


def test_execute_prompt_names_season_criteria():
    text = scaffold.PROMPTS["execute"]
    assert "the season YAML" in text
    assert "`falsification.yaml` (sealed criteria)." not in text
    assert "Do not read or reinterpret the falsification criteria" in text


# --- #28 checker root fallback ------------------------------------------------


def test_checker_root_fallback(tmp_path):
    checker = _load_checker()
    campaign = tmp_path / "campaign"
    (campaign / ".rumpun" / "runs").mkdir(parents=True)
    deep = campaign / "src" / "deep"
    deep.mkdir(parents=True)
    assert checker.find_repo_root(deep) == campaign
    engine_repo = tmp_path / "engine"
    (engine_repo / "src" / "rumpun").mkdir(parents=True)
    deep2 = engine_repo / "a" / "b"
    deep2.mkdir(parents=True)
    assert checker.find_repo_root(deep2) == engine_repo
    with pytest.raises(SystemExit, match=r"\.rumpun or src/rumpun"):
        checker.find_repo_root(tmp_path)


# --- #29 akar correct ---------------------------------------------------------


def test_akar_correct_after_broken_seal(tmp_path):
    akar.append_record(tmp_path, "s9-harvest", "season s9: WIN", "body line\n")
    original = akar.find_record(tmp_path, "s9-harvest")
    original.write_text(
        original.read_text(encoding="utf-8") + "appended after the seal\n",
        encoding="utf-8",
    )
    path = akar.correct_record(
        tmp_path, "s9-harvest", "the harvest cited a curl that never ran"
    )
    text = path.read_text(encoding="utf-8")
    assert "corrects: s9-harvest" in text
    assert "reason: the harvest cited a curl that never ran" in text
    assert "original digest: absent" in text


def test_akar_correct_keeps_digest_when_sealed(tmp_path):
    akar.append_record(tmp_path, "s9-harvest", "season s9: WIN", "body line\n")
    path = akar.correct_record(tmp_path, "s9-harvest", "wrong metric cited")
    text = path.read_text(encoding="utf-8")
    assert "corrects: s9-harvest" in text
    assert "original digest: absent" not in text


def test_lint_hints_ledger_correct(tmp_path):
    akar.append_record(tmp_path, "s9-harvest", "season s9: WIN", "body line\n")
    record = akar.find_record(tmp_path, "s9-harvest")
    record.write_text(
        record.read_text(encoding="utf-8") + "trailing\n", encoding="utf-8"
    )
    with mock.patch.object(lint, "logger") as mock_logger:
        resolves = lint._citation_resolves(
            "ledger:s9-harvest@deadbeefcafe1234", tmp_path
        )
    assert resolves is False
    warned = " ".join(
        str(call) for call in mock_logger.warning.call_args_list
    )
    assert "ledger correct" in warned


# --- #27 resume ---------------------------------------------------------------


def test_resume_after_harvest(tmp_path):
    root = _write_proj(tmp_path)
    _season_state(root, "s1", status="completed")
    _season_state(root, "s2", status="running")
    harvest.harvest_season(root, "s1", "WIN", "ship the api")
    resume_path = root / "resume.md"
    assert resume_path.is_file()
    text = resume_path.read_text(encoding="utf-8")
    assert "s1: completed" in text
    assert "verdict WIN" in text
    assert "implies: ship the api" in text
    assert "s2: running" in text
    assert (root / "events" / "season-harvested-s1.json").is_file()


# --- #30 loop -----------------------------------------------------------------


def test_loop_once_drains_and_idempotent(tmp_path, capsys):
    root = _write_proj(tmp_path)
    _season_state(root, "s1", status="completed")
    loop.emit_event(root, loop.HARVESTED, "s2", "harvest:WIN")
    assert loop.run(root, once=True) == 0
    out = capsys.readouterr().out
    assert '"kind": "season-completed"' in out  # synthesized
    assert '"season": "s1"' in out
    assert '"kind": "season-harvested"' in out
    assert (root / "events" / ".processed").is_file()
    assert loop.run(root, once=True) == 0
    out2 = capsys.readouterr().out
    assert out2 == ""


def test_loop_lock_held_returns_zero(tmp_path):
    root = _write_proj(tmp_path)
    lock = (root / "loop.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        assert loop.run(root, once=True) == 0
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def test_cli_verb_wiring():
    parser = cli.build_parser()
    for argv in (
        ["resume"],
        ["loop", "--once"],
        ["loop", "--exec", "true"],
        ["ledger", "correct", "s9-harvest", "--reason", "r"],
    ):
        assert hasattr(parser.parse_args(argv), "func")
