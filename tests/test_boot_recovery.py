"""Pins for issue #33: the loop reaps seasons a machine restart orphaned."""

from __future__ import annotations

import json
import os
from pathlib import Path

from rumpun import engine, loop


def _proj(tmp_path: Path) -> Path:
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
    for sid in ("s1", "s2", "s3"):
        (root / "seasons" / f"{sid}.yaml").write_text(
            f'id: {sid}\ngoal: "g"\n', encoding="utf-8"
        )
    return root


def _running(root: Path, sid: str, pid: int, proc_start: int | None) -> None:
    state_dir = root / "runs" / sid / "_season"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "state.json").write_text(
        json.dumps(
            {
                "id": sid,
                "status": "running",
                "started_at": 1.0,
                "spawned": {"a1": {"pid": pid, "proc_start": proc_start}},
            }
        ),
        encoding="utf-8",
    )


def test_reaps_dead_orphan_and_emits_event(tmp_path):
    root = _proj(tmp_path)
    _running(root, "s1", pid=1, proc_start=12345)  # pid 1 is not this process
    reaped = engine.recover_orphans(root)
    assert reaped == ["s1"]
    assert engine.read_persisted_status(root, "s1")["status"] == "stopped_restart"
    assert (root / "events" / "season-completed-s1.json").is_file()


def test_spares_live_season(tmp_path):
    root = _proj(tmp_path)
    pid = os.getpid()
    _running(root, "s2", pid=pid, proc_start=engine._proc_start_ticks(pid))
    assert engine.recover_orphans(root) == []
    assert engine.read_persisted_status(root, "s2")["status"] == "running"


def test_spares_empty_spawned_map(tmp_path):
    root = _proj(tmp_path)
    state_dir = root / "runs" / "s3" / "_season"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text(
        json.dumps({"id": "s3", "status": "running", "started_at": 1.0}),
        encoding="utf-8",
    )
    assert engine.recover_orphans(root) == []
    assert engine.read_persisted_status(root, "s3")["status"] == "running"


def test_loop_once_recovers_then_drains(tmp_path, capsys):
    root = _proj(tmp_path)
    _running(root, "s1", pid=1, proc_start=12345)
    assert loop.run(root, once=True) == 0
    out = capsys.readouterr().out
    assert engine.read_persisted_status(root, "s1")["status"] == "stopped_restart"
    assert '"kind": "season-completed"' in out
    assert '"season": "s1"' in out
