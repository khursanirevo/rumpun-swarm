"""s112 w2 pins — the member render names the dissent.

Spec-first pins (red against current code) for the s112 w2 contract
(seasons/s112.yaml, lane panel-dissent): when a member's latest sealed
panel verdict and its harvest verdict both exist and differ, the member
line names both — the s111 panel mark followed by the compact dissent
mark ' dissent:<panel-verdict>', where the panel verdict is the record
status line's first token (the verdict word; a qualifying clause like
the s76 fallback allowance stays in the record, never a dissent). A
member without both sides renders exactly as before: no harvest verdict
row, no panel verdict record, or agreeing verdicts — no invented
dissents. The panel verdict record's sha256 seal is not required for
the dissent: an unsealed record with a status line still names its
dissent (the seal is not what carries the verdict). Epic rows and the
rollup sums never change (s58/s110/s111 shape).
Fixture: the s108 pattern — real season yamls, real verdict rows
(measured 2026-09-20), real sealed ledger records copied from the
campaign tree, and two hand-sealed records via the real
akar.append_record path (the s110 sweep-pin pattern: the s70 gen-3
verdict whose status carries a qualifying clause — the first-token
parse pin — and an s43 panel verdict over a member with run state but
no harvest verdict row — the both-sides pin). Run state is embedded,
never copied from .rumpun/runs/. Helpers carry the _s112dissent_
prefix, so nothing collides with existing defs.
Measured red against the pre-s112 renderer (2026-09-20): the
divergent-members, full-shape, and unsealed pins red for the right
reason (the rendered lines lacked exactly the dissent token); the
clause and both-sides boundary pins green pre-implementation.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from rumpun import akar

# The real seal prefixes, read off the copied records (probe, 2026-09-20).
_S70_HARVEST_SHA8 = "05e6daae"
_S79_HARVEST_SHA8 = "80e83edc"
_S107_SHA8 = "fed94036"
_S12_SHA8 = "b57aedf9"
_P69_3_SHA8 = "51f2d014"  # panel-s69-3-verdict, LOSS
_P74_SHA8 = "44557c25"  # panel-s74-verdict, LOSS
_P79_2_SHA8 = "387fa6ac"  # panel-s79-2-verdict, NEUTRAL

# Run state is gitignored live state (.rumpun/runs/.gitignore `*`): the
# fixture embeds the real values measured at the s111/s112 ground truth
# (2026-09-20): the persisted status field is verbatim "completed" for
# all eight. s1 keeps no run state (the no-state mark case).
_RUN_STATE = {
    "s69": {"id": "s69", "status": "completed"},
    "s70": {"id": "s70", "status": "completed"},
    "s74": {"id": "s74", "status": "completed"},
    "s79": {"id": "s79", "status": "completed"},
    "s106": {"id": "s106", "status": "completed"},
    "s107": {"id": "s107", "status": "completed"},
    "s12": {"id": "s12", "status": "completed"},
    "s43": {"id": "s43", "status": "completed"},
}

# The real last verdict rows per member (measured 2026-09-20). s106 and
# s43 keep no verdict row (the honest other: the both-sides rule's
# harvest half). s69 and s74 ride as other-class (NEUTRAL season rows),
# s79 as WIN — the dissent mark must render on both classes.
_RUN_VERDICTS = {
    "s69": '{"season": "s69", "verdict": "NEUTRAL"}',
    "s70": '{"season": "s70", "verdict": "WIN"}',
    "s74": '{"season": "s74", "verdict": "NEUTRAL"}',
    "s79": '{"season": "s79", "verdict": "WIN"}',
    "s107": '{"season": "s107", "verdict": "WIN"}',
    "s12": '{"season": "s12", "verdict": "LOSS"}',
}

# The real sealed records the fixture copies: four harvest records, three
# sealed panel verdicts, and the s69 family trio (pending request, gen-2
# error, gen-3 verdict — the rerun-generation ground truth).
_LEDGER_FILES = (
    "2026-09-17_s70-harvest.md",
    "2026-09-17_s79-harvest.md",
    "2026-09-19_s107-harvest.md",
    "2026-09-14_s12-harvest.md",
    "2026-09-20_panel-s69.md",
    "2026-09-20_panel-s69-2-error.md",
    "2026-09-20_panel-s69-3-verdict.md",
    "2026-09-17_panel-s70-verdict.md",
    "2026-09-17_panel-s74-verdict.md",
    "2026-09-20_panel-s79-2-verdict.md",
)

# The declared basis, verbatim as the fixture yaml folds it (the `>-`
# scalar folds to exactly this one line).
_BASIS = (
    "the rollup reads the last verdict row per member; s106 rides as other "
    "(the honest unknown): run state present, no verdict row, no "
    "s106-harvest record by design"
)

_EPICS_YAML = (
    "board-arc:\n"
    "  title: the board arc\n"
    "  goal: the second opinion renders beside the basis\n"
    "  basis: >-\n"
    "    the rollup reads the last verdict row per member; s106 rides as other\n"
    "    (the honest unknown): run state present, no verdict row, no\n"
    "    s106-harvest record by design\n"
    "  seasons:\n"
    "  - s69\n"
    "  - s70\n"
    "  - s74\n"
    "  - s79\n"
    "  - s106\n"
    "  - s107\n"
    "campaign:\n"
    "  title: campaign\n"
    "  goal: evolve one step at a time\n"
    "  seasons:\n"
    "  - s1\n"
    "  - s12\n"
    "  - s43\n"
)


def _s112dissent_repo() -> Path:
    """Repo root by the s70 w2 walk-up (pyproject + src/rumpun + DESIGN)."""
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s112dissent_render(root: Path) -> list[str]:
    """The render under test; a missing module fails naming the spec reason."""
    try:
        from rumpun import epics
    except ImportError as exc:
        pytest.fail(f"src/rumpun/epics.py missing/unimportable: {exc}")
    return epics.render(root)


def _s112dissent_seal8(root: Path, rid: str) -> str:
    """The fixture record's sha8, read off the sealed file (probe, never
    assume)."""
    from rumpun import epics

    return epics._seal8(akar.find_record(root, rid))


def _s112dissent_fx(tmp_path: Path, *, unsealed_s74: bool = False) -> Path:
    """The s108 fixture pattern: the campaign's real yamls and records, no
    network, no stubs. unsealed_s74=True strips the sha256 trailer from
    the copied panel-s74-verdict (the record exists, only the seal is
    missing — the dissent survives on the bare id). Two records are
    hand-sealed via the real akar.append_record path (the s110 sweep-pin
    pattern): panel-s70-3-verdict, whose status carries a qualifying
    clause over an agreeing WIN (the first-token parse pin), and
    panel-s43-verdict over a member with run state but no harvest
    verdict row (the both-sides pin)."""
    repo = _s112dissent_repo()
    root = tmp_path / "s112proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "runs").mkdir()
    for sid in ("s1", "s12", "s43", "s69", "s70", "s74", "s79", "s106", "s107"):
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
        src = repo / ".rumpun" / "ledger" / name
        assert src.is_file(), f"fixture source missing: {src}"
        if unsealed_s74 and name.endswith("panel-s74-verdict.md"):
            text = src.read_text(encoding="utf-8").rstrip("\n")
            body = "\n".join(text.splitlines()[:-1]) + "\n"
            (root / "ledger" / name).write_text(body, encoding="utf-8")
        else:
            shutil.copyfile(src, root / "ledger" / name)
    # The two hand-sealed records (the s110 sweep-pin pattern).
    akar.append_record(
        root,
        "panel-s70-3-verdict",
        "panel verdict s70 (WIN under the s112 fixture clause.)",
        "status: WIN under the s112 fixture clause.\n"
        "route: fixture route (bounded 300s)\n"
        "reply:\n"
        "verdict: WIN under the s112 fixture clause.",
    )
    akar.append_record(
        root,
        "panel-s43-verdict",
        "panel verdict s43 (LOSS)",
        "status: LOSS\n"
        "route: fixture route (bounded 300s)\n"
        "reply:\n"
        "verdict: LOSS",
    )
    (root / "epics.yaml").write_text(_EPICS_YAML, encoding="utf-8")
    return root


def test_s112dissent_divergent_members_name_both(tmp_path: Path) -> None:
    """The three real divergences in the fixture name both verdicts: the
    s111 mark, then ' dissent:<panel-verdict>'. s69 and s74 are
    other-class (NEUTRAL season rows vs panel LOSS); s79 is WIN-class
    (WIN vs panel NEUTRAL)."""
    lines = _s112dissent_render(_s112dissent_fx(tmp_path))
    assert (
        f"  s69  other  {_BASIS}  panel-s69-3-verdict@{_P69_3_SHA8} dissent:LOSS"
    ) in lines
    assert (
        f"  s74  other  {_BASIS}  panel-s74-verdict@{_P74_SHA8} dissent:LOSS"
    ) in lines
    assert (
        f"  s79  WIN  s79-harvest@{_S79_HARVEST_SHA8}  "
        f"panel-s79-2-verdict@{_P79_2_SHA8} dissent:NEUTRAL"
    ) in lines


def test_s112dissent_clause_status_is_not_a_dissent(tmp_path: Path) -> None:
    """s70's latest panel verdict (gen-3, hand-sealed) reads 'WIN under
    the s112 fixture clause.': the verdict word is WIN, the harvest
    verdict is WIN, so the line names the gen-3 mark with no dissent
    token — a qualifying clause never manufactures a dissent."""
    root = _s112dissent_fx(tmp_path)
    lines = _s112dissent_render(root)
    sha8 = _s112dissent_seal8(root, "panel-s70-3-verdict")
    line = next(ln for ln in lines if ln.startswith("  s70  "))
    assert line == (
        f"  s70  WIN  s70-harvest@{_S70_HARVEST_SHA8}  "
        f"panel-s70-3-verdict@{sha8}"
    ), line
    assert "dissent" not in line, line


def test_s112dissent_needs_both_sides(tmp_path: Path) -> None:
    """No invented dissents: s43 holds a sealed panel LOSS verdict but no
    harvest verdict row — its line names the s111 mark without a dissent
    token. s106 (no verdict row, no panel record), s107 and s12 (no
    panel record), and the stateless s1 render exactly as before."""
    root = _s112dissent_fx(tmp_path)
    lines = _s112dissent_render(root)
    sha8 = _s112dissent_seal8(root, "panel-s43-verdict")
    assert (
        f"  s43  other  (no declared basis)  panel-s43-verdict@{sha8}"
    ) in lines
    assert f"  s106  other  {_BASIS}" in lines
    assert f"  s107  WIN  s107-harvest@{_S107_SHA8}" in lines
    assert f"  s12  LOSS  s12-harvest@{_S12_SHA8}" in lines
    assert "  s1  no state" in lines
    for ln in lines:
        if ln.startswith(("  s43  ", "  s106  ", "  s107  ", "  s12  ", "  s1  ")):
            assert "dissent" not in ln, ln


def test_s112dissent_full_render_shape(tmp_path: Path) -> None:
    """The whole render over the fixture: epic rows carrying the
    s117 adjusted view beside the s112 sums (s79's NEUTRAL dissent
    qualifies), member lines in numeric order, the
    dissent token only on the three divergent members."""
    root = _s112dissent_fx(tmp_path)
    gen3 = _s112dissent_seal8(root, "panel-s70-3-verdict")
    p43 = _s112dissent_seal8(root, "panel-s43-verdict")
    lines = _s112dissent_render(root)
    assert lines == [
        "board-arc  s69-s107  3 WIN / 0 LOSS / 3 other  "
        "(adjusted: 2 WIN / 0 LOSS / 4 other)  the board arc",
        f"  s69  other  {_BASIS}  panel-s69-3-verdict@{_P69_3_SHA8} dissent:LOSS",
        f"  s70  WIN  s70-harvest@{_S70_HARVEST_SHA8}  panel-s70-3-verdict@{gen3}",
        f"  s74  other  {_BASIS}  panel-s74-verdict@{_P74_SHA8} dissent:LOSS",
        f"  s79  WIN  s79-harvest@{_S79_HARVEST_SHA8}  "
        f"panel-s79-2-verdict@{_P79_2_SHA8} dissent:NEUTRAL",
        f"  s106  other  {_BASIS}",
        f"  s107  WIN  s107-harvest@{_S107_SHA8}",
        "campaign  s1-s43  0 WIN / 1 LOSS / 1 other  campaign  (no state: s1)",
        "  s1  no state",
        f"  s12  LOSS  s12-harvest@{_S12_SHA8}",
        f"  s43  other  (no declared basis)  panel-s43-verdict@{p43}",
    ]


def test_s112dissent_unsealed_record_still_names_dissent(
    tmp_path: Path,
) -> None:
    """A verdict record missing its sha256 trailer still dissents: the
    status line carries the verdict, not the seal. The line names the
    bare record id followed by the dissent token."""
    lines = _s112dissent_render(_s112dissent_fx(tmp_path, unsealed_s74=True))
    assert f"  s74  other  {_BASIS}  panel-s74-verdict dissent:LOSS" in lines
    line = next(ln for ln in lines if ln.startswith("  s74  "))
    assert "@" not in line, line
