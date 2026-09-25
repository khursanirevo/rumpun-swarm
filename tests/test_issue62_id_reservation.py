"""Issue #62: a season id reserved by one yaml refuses a different yaml.

The collision reproduction: two seasons claim one id; the second start
reattached to (or clobbered) the first's run dir. The gate refuses a
foreign yaml before any state write, lock, or spawn. The engine's root
is the .rumpun state dir (cli._project_root returns cfg.parent), so the
fixtures mirror that layout: rumpun.yaml, seasons/, runs/ all inside
root."""

import hashlib
import json

import pytest

from rumpun import engine


def _seed_taken_id(root, sid, sha):
    ws = root / "runs" / sid / "_season"
    ws.mkdir(parents=True)
    (ws / "state.json").write_text(json.dumps({
        "id": sid, "status": "completed", "started_at": 1.0,
        "yaml_sha": sha,
    }), encoding="utf-8")


def _state_dir(tmp_path):
    root = tmp_path / ".rumpun"
    root.mkdir()
    (root / "rumpun.yaml").write_text("routes: {}\n", encoding="utf-8")
    return root


def _write_yaml(root, sid, body="id: sX\nmode: fight\n"):
    yaml_path = root / "seasons" / f"{sid}.yaml"
    yaml_path.parent.mkdir(parents=True)
    yaml_path.write_text(body, encoding="utf-8")
    return yaml_path


def test_foreign_yaml_refuses(tmp_path):
    root = _state_dir(tmp_path)
    yaml_path = _write_yaml(root, "sX")
    _seed_taken_id(root, "sX", "a" * 64)
    with pytest.raises(
        engine.EngineError, match="belongs to a different season yaml",
    ):
        engine.start_season(yaml_path, root)


def test_same_yaml_passes_the_reservation_gate(tmp_path):
    root = _state_dir(tmp_path)
    yaml_path = _write_yaml(root, "sX")
    sha = hashlib.sha256(yaml_path.read_bytes()).hexdigest()
    _seed_taken_id(root, "sX", sha)
    with pytest.raises(Exception) as excinfo:
        engine.start_season(yaml_path, root)
    assert "belongs to a different season yaml" not in str(excinfo.value)


def test_legacy_state_without_sha_stays_compatible(tmp_path):
    root = _state_dir(tmp_path)
    yaml_path = _write_yaml(root, "sX")
    ws = root / "runs" / "sX" / "_season"
    ws.mkdir(parents=True)
    (ws / "state.json").write_text(json.dumps({
        "id": "sX", "status": "completed", "started_at": 1.0,
    }), encoding="utf-8")
    with pytest.raises(Exception) as excinfo:
        engine.start_season(yaml_path, root)
    assert "belongs to a different season yaml" not in str(excinfo.value)
