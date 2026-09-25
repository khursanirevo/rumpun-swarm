"""s118 w1 pins — the assessment seals the adjusted truth.

Spec-first pins (red against current code) for the s118 w1 contract
(seasons/s118.yaml, w1): the decade-6 review residual — "usefulness-s114
preserves WIN totals despite s79's NEUTRAL and s83's INCONCLUSIVE second
opinions". The seal reads the epic rollup's adjusted counts from the
campaign at seal time and carries them in the body beside the raw ones:
one epics section between the basis line and the fronts, one row per
declared epic, the raw WIN/LOSS/other triple verbatim and the adjusted
triple named beside it when any member's dissent qualifies (the s117
rule: a WIN member whose latest dissent is INCONCLUSIVE or NEUTRAL moves
WIN -> other). Nothing is rewritten: raw counts verbatim, the verdict,
basis, fronts, and satisfied inputs unchanged, and a campaign without
epics.yaml seals byte-identical to the s88 shape. The reader gains the
epics rows field (verbatim row strings); records without the section
read back with an empty list. Boundaries pinned: a WIN member whose
dissent is LOSS never adjusts (the s70 hand-sealed boundary), and a
member whose judge verdict is not WIN never adjusts (the s69 boundary).
Fixture: the s111/s112/s117 pattern — real season yamls, real verdict
rows (measured 2026-09-20), real sealed ledger records copied from the
campaign tree, and one hand-sealed boundary record via the real
akar.append_record path; every seal lands in the fixture ledger, never
the real one. Helpers and constants carry the _s118adj_ prefix; nothing
collides with existing defs. Measured red against the pre-s118 seal
before implementation (see .rumpun/runs/s118/w1/notes.md).
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from rumpun import akar

# The real seal prefixes, read off the copied records (probe, 2026-09-20).
_S12_HARVEST_SHA8 = "b57aedf9"
_S69_HARVEST_SHA8 = "b8e5e26f"
_S70_HARVEST_SHA8 = "05e6daae"
_S79_HARVEST_SHA8 = "80e83edc"
_S83_HARVEST_SHA8 = "3b21b3ba"
_P69_3_SHA8 = "51f2d014"  # panel-s69-3-verdict, LOSS
_P70_SHA8 = "bfc47757"  # panel-s70-verdict, WIN
_P79_2_SHA8 = "387fa6ac"  # panel-s79-2-verdict, NEUTRAL
_P83_2_SHA8 = "5319dd4e"  # panel-s83-2-verdict, INCONCLUSIVE

# Run state is gitignored live state (.rumpun/runs/.gitignore `*`): the
# fixture embeds the real values measured 2026-09-20 (the persisted
# status field is verbatim "completed" for all six). s1 keeps no run
# state (the no-state mark case).
_S118ADJ_RUN_STATE = {
    "s12": {"id": "s12", "status": "completed"},
    "s43": {"id": "s43", "status": "completed"},
    "s69": {"id": "s69", "status": "completed"},
    "s70": {"id": "s70", "status": "completed"},
    "s79": {"id": "s79", "status": "completed"},
    "s83": {"id": "s83", "status": "completed"},
}

# The real last verdict rows per member (measured 2026-09-20). s43 keeps
# no verdict row (the honest other: run state, no harvest row). s69
# rides as other-class with a LOSS dissent; s79 and s83 carry the two
# WIN-class dissents the adjustment exists for.
_S118ADJ_RUN_VERDICTS = {
    "s12": '{"season": "s12", "verdict": "LOSS"}',
    "s69": '{"season": "s69", "verdict": "NEUTRAL"}',
    "s70": '{"season": "s70", "verdict": "WIN"}',
    "s79": '{"season": "s79", "verdict": "WIN"}',
    "s83": '{"season": "s83", "verdict": "WIN"}',
}

# The real sealed records the fixture copies: five harvest records, the
# s69 family trio (pending request, gen-2 error, gen-3 verdict), and the
# sealed verdicts for s70, s79-2, and s83-2.
_S118ADJ_LEDGER_FILES = (
    "2026-09-14_s12-harvest.md",
    "2026-09-16_s69-harvest.md",
    "2026-09-17_s70-harvest.md",
    "2026-09-17_s79-harvest.md",
    "2026-09-17_s83-harvest.md",
    "2026-09-20_panel-s69.md",
    "2026-09-20_panel-s69-2-error.md",
    "2026-09-20_panel-s69-3-verdict.md",
    "2026-09-17_panel-s70-verdict.md",
    "2026-09-20_panel-s79-2-verdict.md",
    "2026-09-20_panel-s83-2-verdict.md",
)

# The declared basis, verbatim as the fixture yaml folds it.
_BASIS = "the rollup reads the last verdict row per member"

_S118ADJ_EPICS_YAML = (
    "board-arc:\n"
    "  title: the board arc\n"
    "  goal: the adjusted truth carries into the seal\n"
    f"  basis: {_BASIS}\n"
    "  seasons:\n"
    "  - s12\n"
    "  - s69\n"
    "  - s70\n"
    "  - s79\n"
    "  - s83\n"
    "campaign:\n"
    "  title: campaign\n"
    "  goal: evolve one step at a time\n"
    "  seasons:\n"
    "  - s1\n"
    "  - s43\n"
)

# The assessment inputs, the same shape the s88 close yaml carries. The
# yaml carries no counts: the seal reads them from the campaign itself,
# so a composer can never copy a number wrong.
_S118ADJ_FRONT = {
    "name": "the adjusted truth front",
    "owner": "campaign",
    "basis": "the counts row renders beside the raw ones",
    "next": "the next seal reads them fresh",
}
_S118ADJ_SATISFIED = [
    "the rollup renders the adjusted view and the seal carries it"
]
_S118ADJ_DEFAULT_BASIS = (
    "directive seq 9 - usefulness exhaustion is the stopping criterion;"
    " every front below names its owner and next-action"
)
_S118ADJ_FRONT_LINE = (
    "- the adjusted truth front - owner: campaign."
    " the counts row renders beside the raw ones"
    " Next: the next seal reads them fresh."
)

# The counts rows over the base fixture, byte-exact. The board-arc raw
# triple (3 WIN / 1 LOSS / 1 other) stays verbatim; the adjusted view
# names s79 and s83 moved WIN -> other. The campaign epic (s1 no state,
# s43 the honest other) carries no adjustment, so no adjusted clause.
_S118ADJ_BOARD_ARC_ROW = (
    "- board-arc: 3 WIN / 1 LOSS / 1 other  "
    "(adjusted: 1 WIN / 1 LOSS / 3 other)"
)
_S118ADJ_CAMPAIGN_ROW = "- campaign: 0 WIN / 0 LOSS / 1 other"


def _s118adj_repo() -> Path:
    """Repo root by the s70 w2 walk-up (pyproject + src/rumpun + DESIGN)."""
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s118adj_audit():
    """The audit module under test; a missing module fails naming the reason."""
    try:
        from rumpun import audit
    except ImportError as exc:
        pytest.fail(f"src/rumpun/audit.py missing/unimportable: {exc}")
    return audit


def _s118adj_fx(
    tmp_path: Path,
    *,
    proj: str = "s118proj",
    with_panel: bool = True,
    drop_s83_panel: bool = False,
    only_s69_panel: bool = False,
    append_s70_loss: bool = False,
    with_epics: bool = True,
) -> Path:
    """The s108 fixture pattern: the campaign's real yamls and records, no
    network, no stubs. The knobs follow the s117 pins: with_panel=False
    drops every panel record; drop_s83_panel=True leaves s79 the only
    qualifying member; only_s69_panel=True keeps only the s69 family;
    append_s70_loss=True hand-seals a panel-s70-2-verdict record with
    status LOSS via the real akar.append_record path (the WIN-with-LOSS-
    dissent boundary). with_epics=False builds a campaign without
    epics.yaml (the byte-identical backward half). proj names the
    fixture project dir, so one pin can build two campaigns."""
    repo = _s118adj_repo()
    root = tmp_path / proj / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "runs").mkdir()
    for sid in ("s1", "s12", "s43", "s69", "s70", "s79", "s83"):
        src = repo / ".rumpun" / "seasons" / f"{sid}.yaml"
        assert src.is_file(), f"fixture source missing: {src}"
        shutil.copyfile(src, root / "seasons" / f"{sid}.yaml")
    for sid, state in _S118ADJ_RUN_STATE.items():
        dst = root / "runs" / sid / "_season"
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "state.json").write_text(json.dumps(state), encoding="utf-8")
    for sid, rows in _S118ADJ_RUN_VERDICTS.items():
        (root / "runs" / sid / "verdicts.jsonl").write_text(
            rows + "\n", encoding="utf-8"
        )
    (root / "ledger").mkdir()
    for name in _S118ADJ_LEDGER_FILES:
        if not with_panel and "panel-" in name:
            continue
        if drop_s83_panel and name.endswith("panel-s83-2-verdict.md"):
            continue
        if only_s69_panel and "panel-" in name and not name.startswith(
            "2026-09-20_panel-s69"
        ):
            continue
        src = repo / ".rumpun" / "ledger" / name
        assert src.is_file(), f"fixture source missing: {src}"
        shutil.copyfile(src, root / "ledger" / name)
    if append_s70_loss:
        # The WIN-with-LOSS-dissent boundary record, hand-sealed via the
        # real append path (the s110 sweep-pin pattern).
        akar.append_record(
            root,
            "panel-s70-2-verdict",
            "panel verdict s70 (LOSS)",
            "status: LOSS\n"
            "route: fixture route (bounded 300s)\n"
            "reply:\n"
            "verdict: LOSS",
        )
    if with_epics:
        (root / "epics.yaml").write_text(_S118ADJ_EPICS_YAML, encoding="utf-8")
    return root


def _s118adj_seal(root: Path) -> Path:
    """The seal under test over the fixture campaign (fixture ledger only)."""
    return _s118adj_audit().seal_usefulness_assessment(
        root,
        "s118fx",
        "CONTINUE",
        [_S118ADJ_FRONT],
        satisfied=_S118ADJ_SATISFIED,
    )


def _s118adj_body(path: Path) -> str:
    """The record body: lines[4:-1] between the title header and the seal."""
    return "\n".join(path.read_text(encoding="utf-8").splitlines()[4:-1])


def _s118adj_row(body: str, epic: str) -> str:
    """The body's counts row for epic; a missing row fails naming the
    reason (a missing section reads the same: the counts never rendered)."""
    prefix = f"- {epic}: "
    for line in body.splitlines():
        if line.startswith(prefix):
            return line
    pytest.fail(
        f"no {prefix!r} counts row in the seal body; the epics section "
        f"never rendered:\n{body}"
    )


def test_s118adj_seal_body_carries_both_counts(tmp_path: Path) -> None:
    """The whole body, byte-exact: verdict, basis, the epics section with
    the raw triple verbatim and the adjusted triple beside it, then the
    fronts and satisfied inputs unchanged; the sha trailer digests exactly
    those body bytes."""
    path = _s118adj_seal(_s118adj_fx(tmp_path))
    lines = path.read_text(encoding="utf-8").splitlines()
    expected_body = "\n".join(
        [
            "verdict: CONTINUE",
            f"basis: {_S118ADJ_DEFAULT_BASIS}",
            "epics:",
            _S118ADJ_BOARD_ARC_ROW,
            _S118ADJ_CAMPAIGN_ROW,
            "fronts:",
            _S118ADJ_FRONT_LINE,
            "satisfied (recorded, not fronts):",
            f"- {_S118ADJ_SATISFIED[0]}",
        ]
    )
    assert "\n".join(lines[4:-1]) == expected_body
    assert lines[0] == "# akar record: usefulness-s118fx"
    assert lines[1] == "id: usefulness-s118fx"
    assert lines[3] == (
        "title: CONTINUE (the per-season usefulness assessment over the whole ledger)"
    )
    assert lines[-1] == (
        f"sha256: {hashlib.sha256(expected_body.encode('utf-8')).hexdigest()}"
    )


def test_s118adj_raw_counts_stay_verbatim(tmp_path: Path) -> None:
    """Nothing is rewritten: the counts row opens with the raw rollup
    triple exactly as the board renders it, and the adjusted view is
    named beside it, after the raw counts."""
    path = _s118adj_seal(_s118adj_fx(tmp_path))
    body = _s118adj_body(path)
    row = _s118adj_row(body, "board-arc")
    assert row == _S118ADJ_BOARD_ARC_ROW, row
    assert row.startswith("- board-arc: 3 WIN / 1 LOSS / 1 other  (adjusted: ")
    assert row.endswith("(adjusted: 1 WIN / 1 LOSS / 3 other)"), row


def test_s118adj_each_qualifying_member_shifts(tmp_path: Path) -> None:
    """The adjustment is per member: dropping the s83 verdict leaves s79
    as the only qualifying member, so the adjusted triple shifts exactly
    one WIN and the raw triple stays untouched."""
    path = _s118adj_seal(_s118adj_fx(tmp_path, drop_s83_panel=True))
    body = _s118adj_body(path)
    row = _s118adj_row(body, "board-arc")
    assert row == (
        "- board-arc: 3 WIN / 1 LOSS / 1 other  "
        "(adjusted: 2 WIN / 1 LOSS / 2 other)"
    ), row
    assert _s118adj_row(body, "campaign") == _S118ADJ_CAMPAIGN_ROW


def test_s118adj_loss_dissent_on_win_never_adjusts(tmp_path: Path) -> None:
    """The spec boundary: only INCONCLUSIVE or NEUTRAL dissents adjust.
    s70 hand-sealed as judge WIN with panel LOSS (gen-2): the dissent
    exists (proven off the fixture records), and the adjusted triple
    still matches the base row byte-for-byte — a LOSS dissent renders
    its contradiction without moving a count."""
    root = _s118adj_fx(tmp_path, append_s70_loss=True)
    records = akar.declared_ids(root)
    from rumpun import epics  # the s117 counting surface

    assert epics._dissent_word("s70", "WIN", records) == "LOSS"
    row = _s118adj_row(_s118adj_body(_s118adj_seal(root)), "board-arc")
    assert row == _S118ADJ_BOARD_ARC_ROW, row


def test_s118adj_other_member_never_adjusts(tmp_path: Path) -> None:
    """The other boundary: the adjustment requires a WIN judge verdict.
    Only s69's dissent survives (judge NEUTRAL, panel LOSS): the dissent
    exists, the raw triple keeps all three WINs, and the row carries no
    adjusted clause at all."""
    root = _s118adj_fx(tmp_path, only_s69_panel=True)
    records = akar.declared_ids(root)
    from rumpun import epics

    assert epics._dissent_word("s69", "NEUTRAL", records) == "LOSS"
    body = _s118adj_body(_s118adj_seal(root))
    assert _s118adj_row(body, "board-arc") == (
        "- board-arc: 3 WIN / 1 LOSS / 1 other"
    )
    assert "(adjusted" not in body, body


def test_s118adj_no_epics_seals_byte_identical(tmp_path: Path) -> None:
    """The backward half: a campaign without epics.yaml seals byte-identical
    to the s88 shape — no section, no changed line, the s88 body verbatim."""
    path = _s118adj_seal(_s118adj_fx(tmp_path, with_epics=False))
    body = _s118adj_body(path)
    expected_body = "\n".join(
        [
            "verdict: CONTINUE",
            f"basis: {_S118ADJ_DEFAULT_BASIS}",
            "fronts:",
            _S118ADJ_FRONT_LINE,
            "satisfied (recorded, not fronts):",
            f"- {_S118ADJ_SATISFIED[0]}",
        ]
    )
    assert body == expected_body
    assert "epics:" not in body


def test_s118adj_round_trip_reads_both_counts(tmp_path: Path) -> None:
    """What the seal writes, the reader reads back field-identical: the
    verdict, basis, fronts, and satisfied inputs as sealed, the epics rows
    as verbatim strings; a record without the section reads back with an
    empty epics list."""
    audit = _s118adj_audit()
    with_epics = _s118adj_seal(_s118adj_fx(tmp_path))
    data = audit.read_usefulness_assessment(with_epics)
    assert data["verdict"] == "CONTINUE"
    assert data["basis"] == _S118ADJ_DEFAULT_BASIS
    assert data["fronts"] == [_S118ADJ_FRONT]
    assert data["satisfied"] == _S118ADJ_SATISFIED
    assert data["epics"] == [
        _S118ADJ_BOARD_ARC_ROW[2:],
        _S118ADJ_CAMPAIGN_ROW[2:],
    ]
    without = _s118adj_seal(
        _s118adj_fx(tmp_path, proj="s118proj-noepics", with_epics=False)
    )
    assert audit.read_usefulness_assessment(without)["epics"] == []


def test_s118adj_supersede_carries_the_counts_too(tmp_path: Path) -> None:
    """The basis supersede is a full assessment record: its body carries
    the same epics rows the original sealed, with the corrected basis
    line, and reads back whole through the record contract."""
    audit = _s118adj_audit()
    root = _s118adj_fx(tmp_path)
    original = _s118adj_seal(root)
    superseded = audit.seal_usefulness_assessment(
        root,
        "s118fx",
        "CONTINUE",
        [_S118ADJ_FRONT],
        satisfied=_S118ADJ_SATISFIED,
        basis="the adjusted basis correction",
        supersede=True,
    )
    original_data = audit.read_usefulness_assessment(original)
    superseded_data = audit.read_usefulness_assessment(superseded)
    # The s105 contract: the original's read-back carries the superseding
    # basis and names the superseding record; the -basis record reads as
    # itself (no self-supersede key).
    assert original_data["basis"] == "the adjusted basis correction"
    assert original_data["basis_superseded_by"] == "usefulness-s118fx-basis"
    assert superseded_data["basis"] == "the adjusted basis correction"
    assert superseded_data["epics"] == original_data["epics"]
    assert _S118ADJ_BOARD_ARC_ROW in _s118adj_body(superseded)
