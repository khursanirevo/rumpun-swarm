"""rumpun statusline tests: segment rendering + settings compose."""

import json
from pathlib import Path

from rumpun import statusline


def _seed(root: Path, sid, status, started, agents=None):  # type: ignore[name-defined]
    ws = root / ".rumpun" / "runs" / sid / "_season"
    ws.mkdir(parents=True)
    payload = {"id": sid, "status": status, "started_at": started}
    if agents:
        payload["agents"] = agents
    (ws / "state.json").write_text(json.dumps(payload), encoding="utf-8")


def test_segment_running_and_verdict(tmp_path):
    root = tmp_path
    _seed(root, "s2", "running", 200,
          {"a1": {"state": "run"}, "a2": {"state": "run"}})
    _seed(root, "s1", "completed", 100)
    ledger = root / ".rumpun" / "ledger"
    ledger.mkdir(parents=True)
    (ledger / "2026-09-23_s1-harvest.md").write_text(
        "verdict: WIN\n", encoding="utf-8")
    seg = statusline.segment(root)
    assert "s2 run (a1:run,a2:run)" in seg
    assert "s1 WIN" in seg


def test_segment_empty_without_state(tmp_path):
    assert statusline.segment(tmp_path) == ""


def test_install_composes_and_uninstall_restores(tmp_path):
    claude = tmp_path / "claude"
    claude.mkdir()
    (claude / "settings.json").write_text(json.dumps(
        {"statusLine": {"type": "command", "command": "orig-cmd"}}))
    project = tmp_path / "proj"
    (project / ".rumpun" / "runs").mkdir(parents=True)
    assert statusline.install(claude, project) == 0
    settings = json.loads((claude / "settings.json").read_text())
    assert "rumpun-hud.sh" in settings["statusLine"]["command"]
    wrapper = claude / "hud" / "rumpun-hud.sh"
    assert "orig-cmd" in wrapper.read_text(encoding="utf-8")
    assert statusline.uninstall(claude) == 0
    settings = json.loads((claude / "settings.json").read_text())
    assert settings["statusLine"]["command"] == "orig-cmd"
    assert not wrapper.exists()
