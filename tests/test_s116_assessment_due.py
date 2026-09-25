"""s116 w2 pins -- the planner announces the standing assessment due.

Spec source: the s116 w2 brief (the w2 assessment-due lane in
.rumpun/seasons/s116.yaml) and the seam contract in src/rumpun/evolve.py
(draft_next, the verb behind `rumpun evolve plan`). The s107 -> s114 gap
crossed seven closes before the eighth usefulness record sealed, and only
the close worker noticed -- the duty rode on operator memory. The rule
this season lands: the plan inspects the lineage behind the parent season
(the seasons/<sid>.yaml parent chain), counts the consecutive closes with
no usefulness-<sid> akar record, and when the drought reaches the campaign
cadence (6 closes, the boundary the rule pins; six is exactly the
s108..s113 drought that preceded the s114 seal) the plan output announces
the assessment due and names the last sealed id. A current lineage stays
silent, and the hint never blocks the draft.

Offline: in-process over tmp_path fixture campaigns; records land only in
the tmp campaign ledger through akar.append_record -- the real campaign
ledger is never written, and no season runs.

Grafting: drop this file into tests/. Helpers and constants carry the
_s116 prefix; nothing collides with existing defs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from rumpun import akar, evolve

_S116_CADENCE = 6  # the boundary the rule pins; see the pin1 arithmetic


def _s116_season_text(sid: str, parent_id: str | None) -> str:
    """One draftable lineage season: id, optional parent, methodology.pipeline."""
    lines = [
        f"id: {sid}",
        f'goal: "fixture {sid}"',
        "metric: m",
        "mode: fight",
        "methodology:",
        '  approach: "x"',
        "  evidence: []",
        "  primary_change:",
        "    type: add",
        "    node: execute",
        '    baseline: "b"',
        '    expected_band: "WIN if x"',
        '    rollback: "git revert"',
        f'    eval_window: "{sid}"',
        "  pipeline:",
        "    - phase: execute",
        "      primitive: execute",
        "      agents: writers",
        "      prompt: prompts/dev/dummy.md",
        "      writes: results.jsonl",
    ]
    if parent_id is not None:
        lines.insert(1, f"parent: {parent_id}")
    return "\n".join(lines) + "\n"


def _s116_campaign(
    tmp_path: Path, chain: list[tuple[str, str | None]]
) -> Path:
    """A tmp campaign: seasons/<sid>.yaml files over the .rumpun-state root.

    root is the state dir draft_next resolves through paths.seasons_dir
    (the engine convention). The real campaign ledger is never touched.
    """
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    for sid, parent_id in chain:
        season = root / "seasons" / f"{sid}.yaml"
        season.write_text(_s116_season_text(sid, parent_id), encoding="utf-8")
    return root


def _s116_seal(root: Path, sid: str) -> Path:
    """usefulness-<sid> into the tmp campaign ledger (tmp only, never real)."""
    return akar.append_record(
        root, f"usefulness-{sid}", f"season {sid} assessed", "fixture basis"
    )


def _s116_plan(caplog: pytest.LogCaptureFixture, root: Path, parent_id: str) -> str:
    """Plan the next season from parent_id; the draft must land; return the log."""
    with caplog.at_level(logging.DEBUG, logger="rumpun.evolve"):
        drafted = evolve.draft_next(root, root / "seasons" / f"{parent_id}.yaml")
    assert drafted.is_file(), f"the plan never produced the draft: {drafted}"
    return caplog.text


def test_s116_pin1_drought_at_boundary_announces(tmp_path: Path, caplog: Any) -> None:
    """Red-first: at the cadence boundary the plan announces, naming the seal.

    The s107 -> s114 incident shape: usefulness-s107 is the last seal,
    closes s108..s113 (six) carried none, and the plan of s114 from s113
    announces the assessment due with the last sealed id and the six-close
    count. The hint never blocks the draft.
    """
    root = _s116_campaign(
        tmp_path,
        [
            ("s113", "s112"),
            ("s112", "s111"),
            ("s111", "s110"),
            ("s110", "s109"),
            ("s109", "s108"),
            ("s108", "s107"),
        ],
    )
    _s116_seal(root, "s107")
    text = _s116_plan(caplog, root, "s113")
    assert "assessment due" in text, f"the plan stayed silent: {text!r}"
    assert "usefulness-s107" in text, f"the hint never names the seal: {text!r}"
    assert f"{_S116_CADENCE} closes" in text, (
        f"the hint never states the boundary count: {text!r}"
    )


def test_s116_pin2_below_boundary_silent(tmp_path: Path, caplog: Any) -> None:
    """Green guard: a drought one close short of the boundary stays silent."""
    root = _s116_campaign(
        tmp_path,
        [
            ("s113", "s112"),
            ("s112", "s111"),
            ("s111", "s110"),
            ("s110", "s109"),
            ("s109", "s108"),
            ("s108", "s107"),
        ],
    )
    _s116_seal(root, "s107")
    _s116_seal(root, "s108")
    text = _s116_plan(caplog, root, "s113")
    assert "assessment due" not in text, f"the plan announced early: {text!r}"


def test_s116_pin3_parent_sealed_silent(tmp_path: Path, caplog: Any) -> None:
    """Green guard: the parent carrying the latest seal stays silent."""
    root = _s116_campaign(tmp_path, [("s113", "s112"), ("s112", None)])
    _s116_seal(root, "s113")
    text = _s116_plan(caplog, root, "s113")
    assert "assessment due" not in text, f"the plan announced early: {text!r}"


def test_s116_pin4_no_seal_names_none(tmp_path: Path, caplog: Any) -> None:
    """Red-first: a never-assessed lineage announces with last sealed none.

    The chain runs s108..s113 with the lineage head carrying no parent, so
    the drought is exactly the boundary and the ledger holds no seal at
    all: the hint still fires and names the absence honestly.
    """
    root = _s116_campaign(
        tmp_path,
        [
            ("s113", "s112"),
            ("s112", "s111"),
            ("s111", "s110"),
            ("s110", "s109"),
            ("s109", "s108"),
            ("s108", None),
        ],
    )
    text = _s116_plan(caplog, root, "s113")
    assert "assessment due" in text, f"the plan stayed silent: {text!r}"
    assert "last sealed none" in text, f"the hint invented a seal: {text!r}"
