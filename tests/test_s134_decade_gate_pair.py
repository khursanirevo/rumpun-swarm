"""s134 w1 pins -- the decade gate and the drought hint read record scope.

Spec source: issues #45 and #51 and the two seams (the audit F7 decade
gate, _usefulness_decade_due in src/rumpun/audit.py; the plan hint,
_assessment_due in src/rumpun/evolve.py). Both defects are the same
convention read by count instead of scope: the decade records carry their
audit-time coverage on a `seasons: <int>` line (the runner stamps
"seasons: N season yamls at audit time"), and both gates ignored it.

issue #45: the F7 gate demanded floor(count/10) decade records regardless
of coverage, so one wide record (decade-1 covering s1..s74 in khursani)
left a permanent false nag. The fix: coverage arithmetic -- a review is
due only when USEFULNESS_DECADE_SIZE seasons sit above the covered
frontier; a record with no parseable or in-range scope keeps the
pre-s134 per-record credit (USEFULNESS_DECADE_SIZE * N).

issue #51: the drought walk stopped only at per-season seals, so in a
decade-only ledger the hint fired on every plan with an inflated count
(84 closes when the newest review covered all but 4). The fix: the
no-stopper branch counts only lineage closes above the decade frontier
(the s122 date rule generalized: the review is the fresher judgment for
the closes it covers). The stopper branch keeps the s122 reconciliation
untouched.

Offline: in-process over tmp_path fixture campaigns; records land only
in the tmp campaign ledger through akar.append_record -- the real
campaign ledger is never written, and no season runs.

Grafting: drop this file into tests/. Helpers and constants carry the
_s134 prefix; nothing collides with existing defs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from rumpun import akar, audit, evolve

_S134_DECADY_BODY = "seasons: {n} season yamls at audit time\n"


def _s134_season_text(sid: str, parent_id: str | None) -> str:
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


def _s134_campaign(
    tmp_path: Path, chain: list[tuple[str, str | None]]
) -> Path:
    """A tmp campaign over the .rumpun-state root (the engine convention)."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    for sid, parent_id in chain:
        season = root / "seasons" / f"{sid}.yaml"
        season.write_text(_s134_season_text(sid, parent_id), encoding="utf-8")
    return root


def _s134_chain(top: int) -> list[tuple[str, str | None]]:
    """A lineage s1..s(top) over the state dir, no seals anywhere."""
    return [(f"s{n}", None if n == 1 else f"s{n - 1}") for n in range(1, top + 1)]


def _s134_plan(caplog: pytest.LogCaptureFixture, root: Path, parent_id: str) -> str:
    """Plan the next season from parent_id; the draft must land; return the log."""
    with caplog.at_level(logging.DEBUG, logger="rumpun.evolve"):
        drafted = evolve.draft_next(root, root / "seasons" / f"{parent_id}.yaml")
    assert drafted.is_file(), f"the plan never produced the draft: {drafted}"
    return caplog.text


def _s134_audit_proj(tmp_path: Path, seasons: int) -> Path:
    """A tmp campaign for the F7 gate: seasons/<sid>.yaml x n, no ledger yet."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    for n in range(1, seasons + 1):
        (root / "seasons" / f"s{n}.yaml").write_text(
            _s134_season_text(f"s{n}", None), encoding="utf-8"
        )
    return root


def test_s134_a1_wide_record_ends_the_false_nag(tmp_path: Path) -> None:
    """Red-first (issue #45): one wide decade record covers what it names.

    20 season yamls, usefulness-decade-1 sealed with scope "seasons: 20":
    every closed season is reviewed, so the gate stays silent. The count
    rule (20 // 10 = 2 > 1 record) nags for decade 2 forever -- the
    khursani shape (decade-1 covered s1..s74; 86 yamls demanded decade 4).
    """
    root = _s134_audit_proj(tmp_path, 20)
    akar.append_record(
        root, "usefulness-decade-1", "decade 1 review",
        _S134_DECADY_BODY.format(n=20),
    )
    assert audit._usefulness_decade_due(root) is None, (
        "the gate nags though the record covers every season"
    )


def test_s134_a2_out_of_scope_record_does_not_silence(tmp_path: Path) -> None:
    """Guard: a scope beyond the season count earns no coverage.

    "seasons: 500" over 20 yamls claims seasons that do not exist here;
    the record keeps only the per-record credit (10 * 1), so the ten
    uncovered seasons above it keep the review due for decade 2. The
    reported decade is max(N) + 1, never an id an append would collide
    with.
    """
    root = _s134_audit_proj(tmp_path, 20)
    akar.append_record(
        root, "usefulness-decade-1", "decade 1 review",
        "seasons: 500 season yamls at audit time\n",
    )
    line = audit._usefulness_decade_due(root)
    assert line is not None, "an out-of-scope record silenced the gate"
    assert "decade 2" in line
    assert "20 season yamls, 1 usefulness-decade records" in line


def test_s134_a3_scopeless_record_keeps_old_credit(tmp_path: Path) -> None:
    """Guard: a record with no seasons line keeps the pre-s134 arithmetic.

    Ledger shapes predating the scope line must keep their standing
    credit: usefulness-decade-1 with no parseable scope covers
    USEFULNESS_DECADE_SIZE seasons, so a 10-season campaign with one such
    record stays silent (the test_rumpun pin 1c contract).
    """
    root = _s134_audit_proj(tmp_path, 10)
    akar.append_record(
        root, "usefulness-decade-1", "decade 1 review", "fixture basis"
    )
    assert audit._usefulness_decade_due(root) is None


def test_s134_a4_stale_frontier_re_arms_review(tmp_path: Path) -> None:
    """Red-first (issue #45): the gate reads the newest covered season.

    decade-1 keeps the old per-record credit (10); decade-2 names scope
    19. At 29 yamls the ten seasons s20..s29 sit above the frontier, so
    the review is due for decade 3. The count rule (29 // 10 = 2 <= 2
    records) stayed silent over the uncovered span.
    """
    root = _s134_audit_proj(tmp_path, 29)
    akar.append_record(
        root, "usefulness-decade-1", "decade 1 review", "fixture basis"
    )
    akar.append_record(
        root, "usefulness-decade-2", "decade 2 review",
        _S134_DECADY_BODY.format(n=19),
    )
    line = audit._usefulness_decade_due(root)
    assert line is not None, "ten uncovered seasons raised no review"
    assert "decade 3" in line
    assert "29 season yamls, 2 usefulness-decade records" in line


def test_s134_a5_no_records_nags_at_ten(tmp_path: Path) -> None:
    """Guard: the fresh-campaign shape is unchanged.

    Ten season yamls, no decade records: the gate announces decade 1
    exactly as the s33 rule did.
    """
    root = _s134_audit_proj(tmp_path, 10)
    line = audit._usefulness_decade_due(root)
    assert line is not None, "the first decade review went silent"
    assert "decade 1" in line
    assert "10 season yamls, 0 usefulness-decade records" in line


def test_s134_e1_current_decade_coverage_silences_hint(
    tmp_path: Path, caplog: Any
) -> None:
    """Red-first (issue #51): a decade-only ledger with current coverage.

    Six unsealed closes s1..s6, usefulness-decade-1 sealed with scope 6:
    the review covers every close, so the plan stays silent. The walk
    found no per-season stopper and fired the cadence nag on every plan.
    """
    root = _s134_campaign(tmp_path, _s134_chain(6))
    akar.append_record(
        root, "usefulness-decade-1", "decade 1 review",
        _S134_DECADY_BODY.format(n=6),
    )
    text = _s134_plan(caplog, root, "s6")
    assert "assessment due" not in text, (
        f"the plan nagged past a current decade review: {text!r}"
    )


def test_s134_e2_stale_coverage_counts_uncovered_closes(
    tmp_path: Path, caplog: Any
) -> None:
    """Red-first (issue #51): the hint counts the uncovered drought only.

    Twelve closes s1..s12; usefulness-decade-1 covers through season 6.
    Six closes s7..s12 sit above the frontier, so the hint fires with the
    honest count 6 and names the decade record. The old walk announced
    the full chain (12 closes) no matter how fresh the review was.
    """
    root = _s134_campaign(tmp_path, _s134_chain(12))
    akar.append_record(
        root, "usefulness-decade-1", "decade 1 review",
        _S134_DECADY_BODY.format(n=6),
    )
    text = _s134_plan(caplog, root, "s12")
    assert "assessment due: 6 closes since the last usefulness record" in text, (
        f"the hint lost the honest drought count: {text!r}"
    )
    assert "last sealed usefulness-decade-1" in text


def test_s134_e3_scopeless_record_keeps_old_announce(
    tmp_path: Path, caplog: Any
) -> None:
    """Guard: a scopeless decade record keeps the pre-s134 announcement.

    usefulness-decade-1 with no seasons line keeps the per-record credit
    (10), so all six closes s108..s113 sit above it and the hint fires
    with 6 closes naming the record (the test_s122 pin 2 contract).
    """
    root = _s134_campaign(
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
    text = _s134_plan(caplog, root, "s113")
    assert "assessment due: 6 closes since the last usefulness record" in text, (
        f"the hint changed its shape: {text!r}"
    )
    assert "last sealed usefulness-decade-1" in text


def test_s134_e4_uncovered_below_cadence_stays_silent(
    tmp_path: Path, caplog: Any
) -> None:
    """Red-first (issue #51): the cadence boundary rides the frontier.

    Eleven closes s1..s11; usefulness-decade-1 covers through season 6.
    Five closes sit above it -- one short of the 6-close cadence -- so
    the plan stays silent. The old walk counted the whole chain (11) and
    announced.
    """
    root = _s134_campaign(tmp_path, _s134_chain(11))
    akar.append_record(
        root, "usefulness-decade-1", "decade 1 review",
        _S134_DECADY_BODY.format(n=6),
    )
    text = _s134_plan(caplog, root, "s11")
    assert "assessment due" not in text, (
        f"the plan announced below the cadence: {text!r}"
    )


def test_s134_e5_stopper_path_untouched(tmp_path: Path, caplog: Any) -> None:
    """Guard: the s122 reconciliation survives the generalization.

    usefulness-s107 seals upline and usefulness-decade-1 (scope line and
    all) postdates it on the ledger, so the decade review is the fresher
    judgment and the six unsealed closes s108..s113 stay silent -- via
    the stopper branch, which this fix does not touch.
    """
    root = _s134_campaign(
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
    akar.append_record(
        root, "usefulness-s107", "season s107 assessed", "fixture basis"
    )
    akar.append_record(
        root, "usefulness-decade-1", "decade 1 review",
        _S134_DECADY_BODY.format(n=6),
    )
    text = _s134_plan(caplog, root, "s113")
    assert "assessment due" not in text, (
        f"the stopper reconciliation broke: {text!r}"
    )
