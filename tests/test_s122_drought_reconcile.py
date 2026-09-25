"""s122 w1 pins -- the drought counts every usefulness convention (issue #38).

Spec source: issue #38 and the seam contract in src/rumpun/evolve.py
(_assessment_due, the walk behind the draft_next assessment-due hint).
Two usefulness conventions exist: the per-close seals (usefulness-s<N>)
and the decade reviews (usefulness-decade-<N>, the audit F7 series). The
walk saw only the s-series, so a decade review never stopped the drought
and the announcement could never name one. The reconciliation: a decade
record is a standing usefulness judgment. When the newest decade record
postdates or matches the ledger date of the stopper seal, the decade
review is the fresher judgment and the hint stays silent. The
announcement names the record that stopped the drought, whichever
series it belongs to.

Offline: in-process over tmp_path fixture campaigns; records land only in
the tmp campaign ledger through akar.append_record -- the real campaign
ledger is never written, and no season runs.

Grafting: drop this file into tests/. Helpers and constants carry the
_s122 prefix; nothing collides with existing defs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from rumpun import akar, evolve


def _s122_season_text(sid: str, parent_id: str | None) -> str:
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


def _s122_campaign(
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
        season.write_text(_s122_season_text(sid, parent_id), encoding="utf-8")
    return root


def _s122_seal(root: Path, sid: str) -> Path:
    """usefulness-<sid> into the tmp campaign ledger (tmp only, never real)."""
    return akar.append_record(
        root, f"usefulness-{sid}", f"season {sid} assessed", "fixture basis"
    )


def _s122_plan(caplog: pytest.LogCaptureFixture, root: Path, parent_id: str) -> str:
    """Plan the next season from parent_id; the draft must land; return the log."""
    with caplog.at_level(logging.DEBUG, logger="rumpun.evolve"):
        drafted = evolve.draft_next(root, root / "seasons" / f"{parent_id}.yaml")
    assert drafted.is_file(), f"the plan never produced the draft: {drafted}"
    return caplog.text


def test_s122_pin1_decade_inside_window_silences(tmp_path: Path, caplog: Any) -> None:
    """Red-first: a decade seal inside the window silences the hint.

    issue #38: the decade reviews seal usefulness-decade-<N> records and
    the cadence walk counted only usefulness-s<N>, so a decade review,
    itself a standing usefulness judgment, never stopped the drought.
    usefulness-s107 seals upline; usefulness-decade-1 postdates or
    matches it on the ledger (append_record stamps today on both, so the
    comparison lands on the same-day boundary); the six unsealed closes
    s108..s113 stay silent.
    """
    root = _s122_campaign(
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
    _s122_seal(root, "s107")
    akar.append_record(
        root, "usefulness-decade-1", "decade 1 review", "fixture basis"
    )
    text = _s122_plan(caplog, root, "s113")
    assert "assessment due" not in text, (
        f"the plan announced past the decade seal: {text!r}"
    )


def test_s122_pin2_announcement_names_decade_judgment(
    tmp_path: Path, caplog: Any
) -> None:
    """Red-first: the announcement names the record that stopped the walk.

    With no per-season seal anywhere in the lineage the drought runs the
    whole chain and the walk has no stopper. The last standing judgment
    is the decade-1 review, and the announcement must name it; the old
    rule printed the s-series-only "none".
    """
    root = _s122_campaign(
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
    akar.append_record(
        root, "usefulness-decade-1", "decade 1 review", "fixture basis"
    )
    text = _s122_plan(caplog, root, "s113")
    assert "assessment due" in text, f"the plan stayed silent: {text!r}"
    assert "last sealed usefulness-decade-1" in text, (
        f"the hint never names the decade judgment: {text!r}"
    )


def test_s122_pin3_announcement_names_the_walk_stopper(
    tmp_path: Path, caplog: Any
) -> None:
    """Red-first: the announcement names the stopper, not the ledger max.

    The walk stops at the upline seal usefulness-s107; usefulness-s120
    sits on the ledger from a side lineage and does not speak for this
    chain. The announcement names the record that stopped the drought,
    not the highest-numbered seal the ledger holds.
    """
    root = _s122_campaign(
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
    _s122_seal(root, "s107")
    _s122_seal(root, "s120")
    text = _s122_plan(caplog, root, "s113")
    assert "last sealed usefulness-s107" in text, (
        f"the hint named a record off the drought walk: {text!r}"
    )
    assert "last sealed usefulness-s120" not in text, (
        f"the hint named the ledger max: {text!r}"
    )


def test_s122_pin4_decade_below_boundary_stays_silent(
    tmp_path: Path, caplog: Any
) -> None:
    """Green guard: the decade check rides behind the cadence boundary.

    A drought one close short of the boundary stays silent even with a
    decade review on the ledger: the boundary arithmetic is unchanged
    and the decade record neither shortens nor lengthens the count.
    """
    root = _s122_campaign(
        tmp_path,
        [
            ("s112", "s111"),
            ("s111", "s110"),
            ("s110", "s109"),
            ("s109", "s108"),
            ("s108", "s107"),
        ],
    )
    _s122_seal(root, "s107")
    akar.append_record(
        root, "usefulness-decade-1", "decade 1 review", "fixture basis"
    )
    text = _s122_plan(caplog, root, "s112")
    assert "assessment due" not in text, f"the plan announced early: {text!r}"
