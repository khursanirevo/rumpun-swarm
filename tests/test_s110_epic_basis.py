"""s110 w1 pins — the epic view names each member's basis.

Spec-first pins (red against current code) for the s110 w1 contract (season
goal seasons/s110.yaml: "the epic view names each member's basis so the
fold's honesty renders"): the epics render prints one basis line per member
under each epic row. A WIN or LOSS member names its harvest record as
id@sha8 (the sha256 seal prefix of the <sid>-harvest ledger record); an
other member names the basis string its epic declared, or the honest mark
when nothing is declared; a no-state member keeps its exclusion from the
rollup and gains its own line. The epic rows keep their s58 shape, the
rollup sums, and the (no state:) mark. Fixture: the s108 pattern — real
season yamls, real verdict rows, real sealed ledger records copied from
the campaign tree, no network, no stubs. Measured red against the
pre-s110 renderer before implementation (see .rumpun/runs/s110/w1/notes.md
for the measured red set). Helpers carry the _s110epic_ prefix, so nothing
collides with existing defs.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

# The declared basis, verbatim as the fixture yaml folds it (the `>-`
# scalar folds to exactly this one line).
_BASIS = (
    "the rollup reads the last verdict row per member; s106 rides as other "
    "(the honest unknown): run state present, no verdict row, no "
    "s106-harvest record by design"
)

# The real seal prefixes, read off the copied records (probe, 2026-09-20).
_S107_SHA8 = "fed94036"
_S12_SHA8 = "b57aedf9"

# Run state is gitignored live state (.rumpun/runs/.gitignore `*`): the
# archive extract cannot carry it (the check-s110 DELTA). The fixture
# embeds the real values measured at the s110 close (2026-09-20): the
# persisted status field is verbatim ("completed" for all five), and the
# verdict rows carry the real season+verdict pairs the render reads.
# s12's verdicts.jsonl holds two unit rows before its season row, elided.
_RUN_STATE = {
    "s69": {"id": "s69", "status": "completed"},
    "s107": {"id": "s107", "status": "completed"},
    "s12": {"id": "s12", "status": "completed"},
    "s106": {"id": "s106", "status": "completed"},
    "s43": {"id": "s43", "status": "completed"},
}

_RUN_VERDICTS = {
    "s69": '{"season": "s69", "verdict": "NEUTRAL"}',
    "s107": '{"season": "s107", "verdict": "WIN"}',
    "s12": '{"season": "s12", "verdict": "LOSS"}',
}

# The real sealed harvest records the fixture copies (the WIN and LOSS cases).
_LEDGER_FILES = ("2026-09-19_s107-harvest.md", "2026-09-14_s12-harvest.md")

_EPICS_YAML = (
    "board-arc:\n"
    "  title: the board arc\n"
    "  goal: the board, the lifecycle, the pulled seasons\n"
    "  basis: >-\n"
    "    the rollup reads the last verdict row per member; s106 rides as other\n"
    "    (the honest unknown): run state present, no verdict row, no\n"
    "    s106-harvest record by design\n"
    "  seasons:\n"
    "  - s69\n"
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

_EXPECTED_FULL = [
    "board-arc  s69-s107  1 WIN / 0 LOSS / 2 other  the board arc",
    f"  s69  other  {_BASIS}",
    f"  s106  other  {_BASIS}",
    f"  s107  WIN  s107-harvest@{_S107_SHA8}",
    "campaign  s1-s43  0 WIN / 1 LOSS / 1 other  campaign  (no state: s1)",
    "  s1  no state",
    f"  s12  LOSS  s12-harvest@{_S12_SHA8}",
    "  s43  other  (no declared basis)",
]


def _s110epic_repo() -> Path:
    """Repo root by the s70 w2 walk-up (pyproject + src/rumpun + DESIGN)."""
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s110epic_render(root: Path) -> list[str]:
    """The render under test; a missing module fails naming the spec reason."""
    try:
        from rumpun import epics
    except ImportError as exc:
        pytest.fail(f"src/rumpun/epics.py missing/unimportable: {exc}")
    return epics.render(root)


def _s110epic_fx(tmp_path: Path, *, with_ledger: bool) -> Path:
    """The s108 fixture pattern: the campaign's real yaml and records, no
    network, no stubs. with_ledger=False drops the records so the pins
    hold the honest absence mark (a verdict-backed member with nothing
    sealed)."""
    repo = _s110epic_repo()
    root = tmp_path / "s110proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "runs").mkdir()
    for sid in ("s1", "s12", "s43", "s69", "s106", "s107"):
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
    if with_ledger:
        (root / "ledger").mkdir()
        for name in _LEDGER_FILES:
            src = repo / ".rumpun" / "ledger" / name
            assert src.is_file(), f"fixture source missing: {src}"
            shutil.copyfile(src, root / "ledger" / name)
    (root / "epics.yaml").write_text(_EPICS_YAML, encoding="utf-8")
    return root


def test_s110epic_win_member_line_names_record(tmp_path: Path) -> None:
    """A WIN member's line names its harvest record id@sha8; the epic row
    keeps the s58 shape and the exact rollup."""
    lines = _s110epic_render(_s110epic_fx(tmp_path, with_ledger=True))
    assert f"  s107  WIN  s107-harvest@{_S107_SHA8}" in lines
    assert "board-arc  s69-s107  1 WIN / 0 LOSS / 2 other  the board arc" in lines


def test_s110epic_other_member_lines_name_declared_basis(tmp_path: Path) -> None:
    """An other member's line names the epic's declared basis string — both
    the no-verdict-row case (s106) and the NEUTRAL-verdict case (s69)."""
    lines = _s110epic_render(_s110epic_fx(tmp_path, with_ledger=True))
    assert f"  s106  other  {_BASIS}" in lines
    assert f"  s69  other  {_BASIS}" in lines


def test_s110epic_loss_member_line_names_record(tmp_path: Path) -> None:
    """A LOSS member's line names its harvest record id@sha8, same as WIN."""
    lines = _s110epic_render(_s110epic_fx(tmp_path, with_ledger=True))
    assert f"  s12  LOSS  s12-harvest@{_S12_SHA8}" in lines


def test_s110epic_other_member_without_declared_basis(tmp_path: Path) -> None:
    """An other member under an epic that declares no basis names the
    honest mark, never a guess."""
    lines = _s110epic_render(_s110epic_fx(tmp_path, with_ledger=True))
    assert "  s43  other  (no declared basis)" in lines


def test_s110epic_no_state_member_line_and_row_mark(tmp_path: Path) -> None:
    """The stateless member gains its own line and keeps the row mark and
    its rollup exclusion."""
    lines = _s110epic_render(_s110epic_fx(tmp_path, with_ledger=True))
    assert "  s1  no state" in lines
    assert "campaign  s1-s43  0 WIN / 1 LOSS / 1 other  campaign  (no state: s1)" in lines


def test_s110epic_win_without_record_names_absence(tmp_path: Path) -> None:
    """A WIN member whose harvest record never sealed names the honest
    absence mark; the rollup still counts the WIN."""
    lines = _s110epic_render(_s110epic_fx(tmp_path, with_ledger=False))
    assert "  s107  WIN  no sealed s107-harvest record" in lines
    assert "board-arc  s69-s107  1 WIN / 0 LOSS / 2 other  the board arc" in lines


def test_s110epic_full_render_shape(tmp_path: Path) -> None:
    """The whole render over the fixture: epic rows byte-identical to the
    s58 shape, member lines in numeric order under each epic."""
    lines = _s110epic_render(_s110epic_fx(tmp_path, with_ledger=True))
    assert lines == _EXPECTED_FULL
