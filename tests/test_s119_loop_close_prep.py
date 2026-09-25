"""Pins for s119 w1: the loop tick seals close-prep for finished seasons.

Directive 17 keeps the close (the verdict, the DESIGN entry, the seeding)
with the close worker; the loop only detects the finished season
(status completed, no <sid>-harvest record) and reserves the close by
name, one record per season. Fixture campaigns in tmp only: no harvest
verb runs, no real ledger receives a write.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from rumpun import akar, loop

ENDED = 1789887947.0

RESERVE = "reserve: the verdict and the DESIGN entry are reserved to the close worker"


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
    for sid in ("s1", "s2", "s3", "s4"):
        (root / "seasons" / f"{sid}.yaml").write_text(
            f'id: {sid}\ngoal: "g"\n', encoding="utf-8"
        )
    return root


def _terminal(root: Path, sid: str, status: str) -> None:
    season_dir = root / "runs" / sid / "_season"
    season_dir.mkdir(parents=True, exist_ok=True)
    (season_dir / "state.json").write_text(
        json.dumps(
            {
                "id": sid,
                "status": status,
                "started_at": 1.0,
                "ended_at": ENDED,
            }
        ),
        encoding="utf-8",
    )


def _running(root: Path, sid: str) -> None:
    season_dir = root / "runs" / sid / "_season"
    season_dir.mkdir(parents=True, exist_ok=True)
    (season_dir / "state.json").write_text(
        json.dumps({"id": sid, "status": "running", "started_at": 1.0}),
        encoding="utf-8",
    )


def _harvest(root: Path, sid: str) -> None:
    akar.append_record(root, f"{sid}-harvest", f"season {sid} harvest", "verdict: WIN\n")


def test_tick_seals_close_prep_for_completed_unharvested_season(tmp_path):
    root = _proj(tmp_path)
    _terminal(root, "s1", "completed")
    assert loop.run(root, once=True) == 0
    assert "s1-close-prep" in akar.declared_ids(root)
    text = akar.find_record(root, "s1-close-prep").read_text(encoding="utf-8")
    expected = datetime.fromtimestamp(ENDED, tz=timezone.utc).isoformat(
        timespec="seconds"
    )
    assert f"completed-at: {expected}" in text
    assert "season: s1" in text
    assert "status: completed" in text
    assert RESERVE in text
    assert "s1-harvest" not in akar.declared_ids(root)
    assert not (root / "events" / "season-harvested-s1.json").exists()


def test_seal_is_idempotent(tmp_path):
    root = _proj(tmp_path)
    _terminal(root, "s1", "completed")
    assert loop.run(root, once=True) == 0
    assert loop.run(root, once=True) == 0
    assert len(list((root / "ledger").glob("*s1-close-prep*"))) == 1
    assert "s1-close-prep" in akar.declared_ids(root)


def test_harvested_season_gets_no_close_prep(tmp_path):
    root = _proj(tmp_path)
    _terminal(root, "s2", "completed")
    _harvest(root, "s2")
    assert loop.run(root, once=True) == 0
    assert "s2-close-prep" not in akar.declared_ids(root)


def test_only_completed_status_seals(tmp_path):
    root = _proj(tmp_path)
    _running(root, "s3")
    _terminal(root, "s4", "failed")
    assert loop.run(root, once=True) == 0
    assert "s3-close-prep" not in akar.declared_ids(root)
    assert "s4-close-prep" not in akar.declared_ids(root)
