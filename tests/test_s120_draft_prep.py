"""Pins for s120 w1: the close-prep hands the drafted yaml to the worker.

The close-prep record gains the next season's draft: the loop calls the
planner's own draft_next over a replica of its inputs staged inside the
finished season's run dir, so the draft lands at
runs/<sid>/seasons/s<N+1>.yaml (gitignored live state) and the tracked
seasons/ tree never sees it. The record names the draft path (draft:
none when the planner refuses); one record and one draft per season;
the fill-and-launch duty stays named. Fixture campaigns in tmp only:
no harvest verb runs, no real ledger receives a write.
"""

from __future__ import annotations

import json
from pathlib import Path

from rumpun import akar, loop

ENDED = 1789887947.0

RESERVE = (
    "reserve: the verdict and the DESIGN entry are reserved to the close worker"
)
DUTY = (
    "fill-and-launch: the close worker fills the next season's primary_change "
    "and evidence and launches it; the loop never harvests, seeds, launches, "
    "or commits"
)


def _season_yaml(sid: str, parent: str) -> str:
    return (
        f"id: {sid}\n"
        f"parent: {parent}\n"
        'goal: "g"\n'
        "metric: m\n"
        "mode: fight\n"
        "methodology:\n"
        '  approach: "a"\n'
        "  pipeline:\n"
        "    - name: w1\n"
        "      agents: writers\n"
        "      budget: {minutes: 30}\n"
        "    - name: w2\n"
        "      agents: writers\n"
        "      budget: {minutes: 30}\n"
    )


def _proj(tmp_path: Path, seasons: tuple[str, ...] = ("s1",)) -> Path:
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    (root / "runs").mkdir()
    for sid in seasons:
        parent_num = int(sid[1:]) - 1
        (root / "seasons" / f"{sid}.yaml").write_text(
            _season_yaml(sid, f"s{parent_num}"), encoding="utf-8"
        )
    return root


def _terminal(root: Path, sid: str, status: str = "completed") -> None:
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


def _record(root: Path, sid: str) -> str:
    return akar.find_record(root, f"{sid}-close-prep").read_text(encoding="utf-8")


def test_prep_records_the_drafted_path(tmp_path):
    root = _proj(tmp_path)
    _terminal(root, "s1")
    assert loop.run(root, once=True) == 0
    assert "s1-close-prep" in akar.declared_ids(root)
    text = _record(root, "s1")
    draft = root / "runs" / "s1" / "seasons" / "s2.yaml"
    assert f"draft: {draft}" in text
    assert draft.is_file()
    body = draft.read_text(encoding="utf-8")
    assert body.startswith(
        "# seasons/s2.yaml — drafted by evolve v0 from s1; "
        "fill primary_change + evidence, then apply"
    )
    assert "id: s2" in body
    assert "parent: s1" in body
    assert "primary_change:" in body
    assert "  evidence: []" in body
    # the tracked seasons tree never sees the draft: the loop never seeds
    assert not (root / "seasons" / "s2.yaml").exists()


def test_record_names_fill_and_launch_duty(tmp_path):
    root = _proj(tmp_path)
    _terminal(root, "s1")
    assert loop.run(root, once=True) == 0
    text = _record(root, "s1")
    assert RESERVE in text
    assert DUTY in text


def test_draft_id_respects_rejected_high_water(tmp_path):
    root = _proj(tmp_path)
    rejected = root / "seasons" / "rejected"
    rejected.mkdir()
    (rejected / "s2.yaml").write_text(
        'id: s2\nparent: s1\ngoal: "g"\n', encoding="utf-8"
    )
    _terminal(root, "s1")
    assert loop.run(root, once=True) == 0
    draft = root / "runs" / "s1" / "seasons" / "s3.yaml"
    assert draft.is_file()
    body = draft.read_text(encoding="utf-8")
    assert "id: s3" in body
    assert "parent: s1" in body
    assert f"draft: {draft}" in _record(root, "s1")
    assert not (root / "seasons" / "s3.yaml").exists()


def test_second_tick_changes_nothing(tmp_path):
    root = _proj(tmp_path)
    _terminal(root, "s1")
    assert loop.run(root, once=True) == 0
    draft = root / "runs" / "s1" / "seasons" / "s2.yaml"
    first = draft.read_bytes()
    assert loop.run(root, once=True) == 0
    records = list((root / "ledger").glob("*s1-close-prep*"))
    assert len(records) == 1
    assert draft.read_bytes() == first
    staged = sorted(
        p.name for p in (root / "runs" / "s1" / "seasons").glob("s*.yaml")
    )
    assert staged == ["s1.yaml", "s2.yaml"]


def test_crash_between_draft_and_record_reuses_the_draft(tmp_path, monkeypatch):
    root = _proj(tmp_path)
    _terminal(root, "s1")

    def _boom(*args, **kwargs):
        raise akar.AkarError("ledger refused")

    monkeypatch.setattr(akar, "append_record", _boom)
    assert loop.run(root, once=True) == 0
    monkeypatch.undo()
    draft = root / "runs" / "s1" / "seasons" / "s2.yaml"
    assert draft.is_file()
    assert "s1-close-prep" not in akar.declared_ids(root)
    first = draft.read_bytes()
    assert loop.run(root, once=True) == 0
    assert "s1-close-prep" in akar.declared_ids(root)
    assert len(list((root / "ledger").glob("*s1-close-prep*"))) == 1
    assert draft.read_bytes() == first


def test_not_latest_parent_seals_draft_none(tmp_path):
    root = _proj(tmp_path, seasons=("s1", "s2"))
    _terminal(root, "s1")
    assert loop.run(root, once=True) == 0
    text = _record(root, "s1")
    assert "draft: none" in text
    # the refusal precedes any staging: no run-dir seasons tree appears
    assert not (root / "runs" / "s1" / "seasons").exists()


def test_malformed_parent_seals_draft_none(tmp_path):
    root = _proj(tmp_path)
    (root / "seasons" / "s1.yaml").write_text(
        'id: s1\nparent: s0\ngoal: "g"\n', encoding="utf-8"
    )
    _terminal(root, "s1")
    assert loop.run(root, once=True) == 0
    text = _record(root, "s1")
    assert "draft: none" in text
    assert not (root / "runs" / "s1" / "seasons" / "s2.yaml").exists()
