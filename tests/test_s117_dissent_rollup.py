"""s117 w1 pins — the rollup renders the dissent adjustment.

Spec-first pins (red against current code) for the s117 w1 contract
(seasons/s117.yaml, w1): the decade-6 review residual — the rollup keeps
WIN totals despite s79's NEUTRAL and s83's INCONCLUSIVE second opinions.
The counts stay honest (the raw WIN/LOSS/other segment stays verbatim);
beside them the epic row gains the adjusted view. A member whose judge
verdict is WIN and whose latest dissent is INCONCLUSIVE or NEUTRAL moves
from WIN to other in the adjusted counts — the row renders
'  (adjusted: W WIN / L LOSS / O other)' between the counts and the
title. The raw counts are never rewritten, the member lines never change
(the s112 dissent marks stay on the member lines), and an epic with no
qualifying member renders byte-identical to the s58 shape.
Boundaries pinned: a member whose dissent is LOSS never adjusts (the
real s77: judge WIN, panel LOSS — the contradiction renders on the
member line only), and a member whose judge verdict is not WIN never
adjusts (the real s69: other with dissent:LOSS). Fixture: the s111/s112
pattern — real season yamls, real verdict rows (measured 2026-09-20),
real sealed ledger records copied from the campaign tree, and one
hand-sealed boundary record via the real akar.append_record path; no
network, no stubs. Helpers carry the _s117dissent_ prefix. Measured red
against the pre-s117 renderer before implementation (see
.rumpun/runs/s117/w1/notes.md for the measured red set).
"""

from __future__ import annotations

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
_RUN_STATE = {
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
_RUN_VERDICTS = {
    "s12": '{"season": "s12", "verdict": "LOSS"}',
    "s69": '{"season": "s69", "verdict": "NEUTRAL"}',
    "s70": '{"season": "s70", "verdict": "WIN"}',
    "s79": '{"season": "s79", "verdict": "WIN"}',
    "s83": '{"season": "s83", "verdict": "WIN"}',
}

# The real sealed records the fixture copies: five harvest records, the
# s69 family trio (pending request, gen-2 error, gen-3 verdict), and the
# sealed verdicts for s70, s79-2, and s83-2.
_LEDGER_FILES = (
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

_EPICS_YAML = (
    "board-arc:\n"
    "  title: the board arc\n"
    "  goal: the dissent adjustment renders beside the counts\n"
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

# The full render, byte-exact (the s111/s112 pattern). The raw counts
# stay verbatim; the adjusted view renders beside them because s79 and
# s83 qualify (judge WIN, dissent NEUTRAL / INCONCLUSIVE). The member
# lines keep the exact s112 shape; the campaign epic (no dissent
# anywhere) renders byte-identical to the s58 shape.
_EXPECTED_ADJUSTED = [
    "board-arc  s12-s83  3 WIN / 1 LOSS / 1 other  "
    "(adjusted: 1 WIN / 1 LOSS / 3 other)  the board arc",
    f"  s12  LOSS  s12-harvest@{_S12_HARVEST_SHA8}",
    f"  s69  other  {_BASIS}  panel-s69-3-verdict@{_P69_3_SHA8} dissent:LOSS",
    f"  s70  WIN  s70-harvest@{_S70_HARVEST_SHA8}  panel-s70-verdict@{_P70_SHA8}",
    f"  s79  WIN  s79-harvest@{_S79_HARVEST_SHA8}  "
    f"panel-s79-2-verdict@{_P79_2_SHA8} dissent:NEUTRAL",
    f"  s83  WIN  s83-harvest@{_S83_HARVEST_SHA8}  "
    f"panel-s83-2-verdict@{_P83_2_SHA8} dissent:INCONCLUSIVE",
    "campaign  s1-s43  0 WIN / 0 LOSS / 1 other  campaign  (no state: s1)",
    "  s1  no state",
    "  s43  other  (no declared basis)",
]

# Dropping every panel record removes the marks and the adjustment: the
# exact s58 shape, the members-without-dissents half of the contract.
_EXPECTED_WITHOUT_PANEL = [
    "board-arc  s12-s83  3 WIN / 1 LOSS / 1 other  the board arc",
    f"  s12  LOSS  s12-harvest@{_S12_HARVEST_SHA8}",
    f"  s69  other  {_BASIS}",
    f"  s70  WIN  s70-harvest@{_S70_HARVEST_SHA8}",
    f"  s79  WIN  s79-harvest@{_S79_HARVEST_SHA8}",
    f"  s83  WIN  s83-harvest@{_S83_HARVEST_SHA8}",
    "campaign  s1-s43  0 WIN / 0 LOSS / 1 other  campaign  (no state: s1)",
    "  s1  no state",
    "  s43  other  (no declared basis)",
]


def _s117dissent_repo() -> Path:
    """Repo root by the s70 w2 walk-up (pyproject + src/rumpun + DESIGN)."""
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s117dissent_render(root: Path) -> list[str]:
    """The render under test; a missing module fails naming the spec reason."""
    try:
        from rumpun import epics
    except ImportError as exc:
        pytest.fail(f"src/rumpun/epics.py missing/unimportable: {exc}")
    return epics.render(root)


def _s117dissent_seal8(root: Path, rid: str) -> str:
    """The sha256 seal prefix of the record rid (the appended boundary
    record), read back off the file."""
    for path in (root / "ledger").iterdir():
        if f"_{rid}.md" in path.name:
            lines = path.read_text(encoding="utf-8").rstrip("\n").splitlines()
            seal = lines[-1]
            assert seal.startswith("sha256: "), path
            return seal[len("sha256: "):].strip()[:8]
    pytest.fail(f"record {rid} not found in the fixture ledger")


def _s117dissent_fx(
    tmp_path: Path,
    *,
    with_panel: bool = True,
    drop_s83_panel: bool = False,
    only_s69_panel: bool = False,
    append_s70_loss: bool = False,
) -> Path:
    """The s108 fixture pattern: the campaign's real yamls and records, no
    network, no stubs. with_panel=False drops every panel record; the pins
    hold the pre-s111 byte shape for every member. drop_s83_panel=True
    drops only the s83 verdict (one qualifying member left). only_s69_
    panel=True keeps only the s69 family (no WIN-class dissent left).
    append_s70_loss=True hand-seals a panel-s70-2-verdict record with
    status LOSS via the real akar.append_record path (the s110 sweep-pin
    pattern): the WIN-with-LOSS-dissent boundary."""
    repo = _s117dissent_repo()
    root = tmp_path / "s117proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "runs").mkdir()
    for sid in ("s1", "s12", "s43", "s69", "s70", "s79", "s83"):
        src = repo / ".rumpun" / "seasons" / f"{sid}.yaml"
        assert src.is_file(), f"fixture source missing: {src}"
        shutil.copyfile(src, root / "seasons" / f"{sid}.yaml")
    for sid, state in _RUN_STATE.items():
        dst = root / "runs" / sid / "_season"
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "state.json").write_text(json.dumps(state), encoding="utf-8")
    for sid, rows in _RUN_VERDICTS.items():
        (root / "runs" / sid / "verdicts.jsonl").write_text(
            rows + "\n", encoding="utf-8"
        )
    (root / "ledger").mkdir()
    for name in _LEDGER_FILES:
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
    (root / "epics.yaml").write_text(_EPICS_YAML, encoding="utf-8")
    return root


def test_s117dissent_adjusted_view_beside_the_counts(tmp_path: Path) -> None:
    """The whole render over the base fixture, byte-exact: the board-arc
    row carries the raw counts verbatim, then the adjusted view beside
    them (s79 NEUTRAL and s83 INCONCLUSIVE move WIN -> other), then the
    title; the member lines keep the exact s112 shape; the campaign epic
    (no dissent anywhere) renders byte-identical to the s58 shape."""
    lines = _s117dissent_render(_s117dissent_fx(tmp_path))
    assert lines == _EXPECTED_ADJUSTED


def test_s117dissent_raw_counts_stay_verbatim(tmp_path: Path) -> None:
    """Nothing is rewritten: the epic row still opens with the raw harvest
    counts exactly as the s58 shape renders them, and the adjusted view
    coexists on the same line after them."""
    lines = _s117dissent_render(_s117dissent_fx(tmp_path))
    row = next(ln for ln in lines if ln.startswith("board-arc  "))
    assert row.startswith(
        "board-arc  s12-s83  3 WIN / 1 LOSS / 1 other  "
        "(adjusted: 1 WIN / 1 LOSS / 3 other)  "
    ), row
    assert row.endswith("the board arc"), row


def test_s117dissent_each_qualifying_member_shifts(tmp_path: Path) -> None:
    """The adjustment is per member: dropping the s83 verdict leaves s79
    as the only qualifying member, so the adjusted view shifts exactly
    one WIN and names s79's dissent only — the counts track the real
    dissent set, never a fixed delta."""
    root = _s117dissent_fx(tmp_path, drop_s83_panel=True)
    lines = _s117dissent_render(root)
    row = next(ln for ln in lines if ln.startswith("board-arc  "))
    assert row == (
        "board-arc  s12-s83  3 WIN / 1 LOSS / 1 other  "
        "(adjusted: 2 WIN / 1 LOSS / 2 other)  the board arc"
    ), row
    assert (
        f"  s83  WIN  s83-harvest@{_S83_HARVEST_SHA8}"
    ) in lines
    assert (
        f"  s79  WIN  s79-harvest@{_S79_HARVEST_SHA8}  "
        f"panel-s79-2-verdict@{_P79_2_SHA8} dissent:NEUTRAL"
    ) in lines


def test_s117dissent_loss_dissent_on_win_never_adjusts(tmp_path: Path) -> None:
    """The spec boundary: only INCONCLUSIVE or NEUTRAL dissents adjust.
    s70 hand-sealed as judge WIN with panel LOSS (gen-2): the member line
    names the dissent (the s112 contract), but the adjusted view leaves
    the WIN in place — the row matches the base row byte-for-byte."""
    root = _s117dissent_fx(tmp_path, append_s70_loss=True)
    lines = _s117dissent_render(root)
    sha8 = _s117dissent_seal8(root, "panel-s70-2-verdict")
    assert (
        f"  s70  WIN  s70-harvest@{_S70_HARVEST_SHA8}  "
        f"panel-s70-2-verdict@{sha8} dissent:LOSS"
    ) in lines
    row = next(ln for ln in lines if ln.startswith("board-arc  "))
    assert row == (
        "board-arc  s12-s83  3 WIN / 1 LOSS / 1 other  "
        "(adjusted: 1 WIN / 1 LOSS / 3 other)  the board arc"
    ), row


def test_s117dissent_other_member_with_dissent_never_adjusts(
    tmp_path: Path,
) -> None:
    """The other boundary: the adjustment requires a WIN judge verdict.
    Only s69's dissent survives (other-class NEUTRAL vs panel LOSS): the
    member line keeps the dissent mark, the epic row loses the adjusted
    view entirely — byte-identical to the s58 shape."""
    lines = _s117dissent_render(_s117dissent_fx(tmp_path, only_s69_panel=True))
    assert (
        f"  s69  other  {_BASIS}  panel-s69-3-verdict@{_P69_3_SHA8} dissent:LOSS"
    ) in lines
    row = next(ln for ln in lines if ln.startswith("board-arc  "))
    assert row == (
        "board-arc  s12-s83  3 WIN / 1 LOSS / 1 other  the board arc"
    ), row
    assert "adjusted" not in row, row


def test_s117dissent_no_dissents_row_byte_identical(tmp_path: Path) -> None:
    """An epic with no dissents renders exactly as before: the full
    without-panel render is the s58 shape and no line carries an
    adjusted token anywhere."""
    lines = _s117dissent_render(_s117dissent_fx(tmp_path, with_panel=False))
    assert lines == _EXPECTED_WITHOUT_PANEL
    for line in lines:
        assert "adjusted" not in line, line
