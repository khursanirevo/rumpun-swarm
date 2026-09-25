"""s111 w1 pins — the epic member render names its second opinion.

Spec-first pins (red against current code) for the s111 w1 contract (season
goal seasons/s111.yaml, lane epic-panel): a member whose panel family holds
a sealed panel-<sid>[-<gen>]-verdict record names it beside its basis — the
compact mark '<record-id>@<sha8>' (the s110 basis format: the record's
sha256 seal prefix), the s108 rerun generation convention with the highest
verdict generation winning. A family whose newest records are an error or a
pending request still names its latest sealed verdict (an error never
hides a sealed verdict). A member with no verdict record in its family
stays honest: no mark, no invented verdict. A verdict record missing its
sha256 trailer names its bare record id (the record exists; only the seal
is missing). Epic rows and the rollup sums never change (s58/s110 shape).
Fixture: the s108 pattern — real season yamls, real verdict rows (measured
2026-09-20), real sealed ledger records copied from the campaign tree, and
the rerun-generation records hand-sealed via the real akar.append_record
path (the s110 sweep-pin pattern); no network, no stubs. Measured red
against the pre-s111 renderer before implementation (see
.rumpun/runs/s111/w1/notes.md for the measured red set). Helpers carry the
_s111panel_ prefix, so nothing collides with existing defs.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from rumpun import akar

# The declared basis, verbatim as the fixture yaml folds it (the `>-`
# scalar folds to exactly this one line).
_BASIS = (
    "the rollup reads the last verdict row per member; s106 rides as other "
    "(the honest unknown): run state present, no verdict row, no "
    "s106-harvest record by design"
)

# The real seal prefixes, read off the copied records (probe, 2026-09-20).
_S70_HARVEST_SHA8 = "05e6daae"
_S107_SHA8 = "fed94036"
_S12_SHA8 = "b57aedf9"
_P70_SHA8 = "bfc47757"  # panel-s70-verdict, WIN
_P74_SHA8 = "44557c25"  # panel-s74-verdict, LOSS
_P69_3_SHA8 = "51f2d014"  # panel-s69-3-verdict

# Run state is gitignored live state (.rumpun/runs/.gitignore `*`): the
# fixture embeds the real values measured at the s110/s111 ground truth
# (2026-09-20): the persisted status field is verbatim "completed" for all
# seven. s1 keeps no run state (the no-state mark case).
_RUN_STATE = {
    "s69": {"id": "s69", "status": "completed"},
    "s70": {"id": "s70", "status": "completed"},
    "s74": {"id": "s74", "status": "completed"},
    "s106": {"id": "s106", "status": "completed"},
    "s107": {"id": "s107", "status": "completed"},
    "s12": {"id": "s12", "status": "completed"},
    "s43": {"id": "s43", "status": "completed"},
}

# The real last verdict rows per member (measured 2026-09-20). s74 rides as
# other-class (its season row is NEUTRAL — the panel LOSS verdict the mark
# names is exactly the second opinion about that NEUTRAL); s69 NEUTRAL.
_RUN_VERDICTS = {
    "s69": '{"season": "s69", "verdict": "NEUTRAL"}',
    "s70": '{"season": "s70", "verdict": "WIN"}',
    "s74": '{"season": "s74", "verdict": "NEUTRAL"}',
    "s107": '{"season": "s107", "verdict": "WIN"}',
    "s12": '{"season": "s12", "verdict": "LOSS"}',
}

# The real sealed records the fixture copies: three harvest records, two
# sealed panel verdicts, and the s69 family trio (pending request, gen-2
# error, gen-3 verdict — the rerun-generation ground truth).
_LEDGER_FILES = (
    "2026-09-17_s70-harvest.md",
    "2026-09-19_s107-harvest.md",
    "2026-09-14_s12-harvest.md",
    "2026-09-17_panel-s70-verdict.md",
    "2026-09-17_panel-s74-verdict.md",
    "2026-09-20_panel-s69.md",
    "2026-09-20_panel-s69-2-error.md",
    "2026-09-20_panel-s69-3-verdict.md",
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

# s112 moved the divergent member lines: the dissent mark names both
# verdicts, so the s69/s74 lines carry ' dissent:LOSS' (measured 2026-09-20).
_EXPECTED_WITH_PANEL = [
    "board-arc  s69-s107  2 WIN / 0 LOSS / 3 other  the board arc",
    f"  s69  other  {_BASIS}  panel-s69-3-verdict@{_P69_3_SHA8} dissent:LOSS",
    f"  s70  WIN  s70-harvest@{_S70_HARVEST_SHA8}  panel-s70-verdict@{_P70_SHA8}",
    f"  s74  other  {_BASIS}  panel-s74-verdict@{_P74_SHA8} dissent:LOSS",
    f"  s106  other  {_BASIS}",
    f"  s107  WIN  s107-harvest@{_S107_SHA8}",
    "campaign  s1-s43  0 WIN / 1 LOSS / 1 other  campaign  (no state: s1)",
    "  s1  no state",
    f"  s12  LOSS  s12-harvest@{_S12_SHA8}",
    "  s43  other  (no declared basis)",
]

_EXPECTED_WITHOUT_PANEL = [
    "board-arc  s69-s107  2 WIN / 0 LOSS / 3 other  the board arc",
    f"  s69  other  {_BASIS}",
    f"  s70  WIN  s70-harvest@{_S70_HARVEST_SHA8}",
    f"  s74  other  {_BASIS}",
    f"  s106  other  {_BASIS}",
    f"  s107  WIN  s107-harvest@{_S107_SHA8}",
    "campaign  s1-s43  0 WIN / 1 LOSS / 1 other  campaign  (no state: s1)",
    "  s1  no state",
    f"  s12  LOSS  s12-harvest@{_S12_SHA8}",
    "  s43  other  (no declared basis)",
]


def _s111panel_repo() -> Path:
    """Repo root by the s70 w2 walk-up (pyproject + src/rumpun + DESIGN)."""
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s111panel_render(root: Path) -> list[str]:
    """The render under test; a missing module fails naming the spec reason."""
    try:
        from rumpun import epics
    except ImportError as exc:
        pytest.fail(f"src/rumpun/epics.py missing/unimportable: {exc}")
    return epics.render(root)


def _s111panel_fx(
    tmp_path: Path, *, with_panel: bool = True, unsealed_s74: bool = False
) -> Path:
    """The s108 fixture pattern: the campaign's real yamls and records, no
    network, no stubs. with_panel=False drops the panel records, so the
    pins hold the pre-s111 byte shape for every member. The s70
    gen-2 rerun family (pending request + error) is hand-sealed via the
    real akar.append_record path (the s110 sweep-pin pattern): it proves
    the newest VERDICT generation wins even when a newer generation holds
    only an error. unsealed_s74=True strips the sha256 trailer from the
    copied panel-s74-verdict (the malformed-record case: the id declares,
    the seal is missing)."""
    repo = _s111panel_repo()
    root = tmp_path / "s111proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "runs").mkdir()
    for sid in ("s1", "s12", "s43", "s69", "s70", "s74", "s106", "s107"):
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
        src = repo / ".rumpun" / "ledger" / name
        assert src.is_file(), f"fixture source missing: {src}"
        if unsealed_s74 and name.endswith("panel-s74-verdict.md"):
            text = src.read_text(encoding="utf-8").rstrip("\n")
            body = "\n".join(text.splitlines()[:-1]) + "\n"
            (root / "ledger" / name).write_text(body, encoding="utf-8")
        else:
            shutil.copyfile(src, root / "ledger" / name)
    if with_panel:
        # The s70 gen-2 rerun family, hand-sealed via the real append path.
        akar.append_record(
            root,
            "panel-s70-2",
            "panel review request: s70 (the s111 fixture rerun)",
            "status: pending\nroute: fixture route (bounded 300s); the "
            "outcome seals as panel-s70-2-verdict or panel-s70-2-error",
        )
        akar.append_record(
            root,
            "panel-s70-2-error",
            "panel outcome panel-s70-2-error",
            "status: pending\nerror: the s111 fixture rerun errored before "
            "a verdict (hand-sealed via the real append path)",
        )
    (root / "epics.yaml").write_text(_EPICS_YAML, encoding="utf-8")
    return root


def test_s111panel_win_member_names_latest_verdict(tmp_path: Path) -> None:
    """A WIN member's line names its harvest record id@sha8 AND its sealed
    panel verdict record id@sha8; the epic row keeps the s58 shape and the
    exact rollup."""
    lines = _s111panel_render(_s111panel_fx(tmp_path))
    assert (
        f"  s70  WIN  s70-harvest@{_S70_HARVEST_SHA8}  "
        f"panel-s70-verdict@{_P70_SHA8}"
    ) in lines
    assert "board-arc  s69-s107  2 WIN / 0 LOSS / 3 other  the board arc" in lines


def test_s111panel_rerun_generation_wins(tmp_path: Path) -> None:
    """The s69 family holds a pending request, a gen-2 error, and a gen-3
    verdict: the line names the gen-3 record, never the never-answered
    request and never the error."""
    lines = _s111panel_render(_s111panel_fx(tmp_path))
    line = next(ln for ln in lines if ln.startswith("  s69  "))
    assert line.endswith(f"panel-s69-3-verdict@{_P69_3_SHA8} dissent:LOSS"), line
    assert "panel-s69 " not in line, line
    assert "panel-s69-2" not in line, line


def test_s111panel_other_member_with_verdict_names_it(tmp_path: Path) -> None:
    """An other-class member (the season row is NEUTRAL) still names its
    sealed panel verdict beside the declared basis: the second opinion
    about that NEUTRAL renders with the fold."""
    lines = _s111panel_render(_s111panel_fx(tmp_path))
    assert f"  s74  other  {_BASIS}  panel-s74-verdict@{_P74_SHA8} dissent:LOSS" in lines


def test_s111panel_error_never_hides_older_verdict(tmp_path: Path) -> None:
    """The s70 family holds the gen-1 verdict plus a gen-2 pending request
    and error: the line names the gen-1 verdict — a newer generation with
    no verdict never hides the sealed one."""
    lines = _s111panel_render(_s111panel_fx(tmp_path))
    line = next(ln for ln in lines if ln.startswith("  s70  "))
    assert f"panel-s70-verdict@{_P70_SHA8}" in line, line
    assert "panel-s70-2" not in line, line


def test_s111panel_no_family_stays_honest(tmp_path: Path) -> None:
    """Members with no panel verdict record keep the exact s110 lines: no
    mark, no invented verdict, the stateless line untouched."""
    lines = _s111panel_render(_s111panel_fx(tmp_path))
    assert f"  s106  other  {_BASIS}" in lines
    assert f"  s107  WIN  s107-harvest@{_S107_SHA8}" in lines
    assert f"  s12  LOSS  s12-harvest@{_S12_SHA8}" in lines
    assert "  s43  other  (no declared basis)" in lines
    assert "  s1  no state" in lines
    for line in lines:
        if any(line.startswith(f"  {sid}  ") for sid in ("s106", "s107", "s12", "s43", "s1")):
            assert "panel-" not in line, line


def test_s111panel_full_render_shape(tmp_path: Path) -> None:
    """The whole render over the fixture: epic rows byte-identical to the
    s58 shape, member lines in numeric order, panel marks only where a
    sealed verdict exists."""
    lines = _s111panel_render(_s111panel_fx(tmp_path))
    assert lines == _EXPECTED_WITH_PANEL


def test_s111panel_without_panel_records_render_unchanged(tmp_path: Path) -> None:
    """An empty ledger renders the exact pre-s111 byte shape: the marks
    never appear without real records behind them."""
    lines = _s111panel_render(_s111panel_fx(tmp_path, with_panel=False))
    assert lines == _EXPECTED_WITHOUT_PANEL


def test_s111panel_unsealed_verdict_names_bare_id(tmp_path: Path) -> None:
    """A verdict record missing its sha256 trailer names its bare record
    id — the record exists, only the seal is missing; no invented digest."""
    lines = _s111panel_render(_s111panel_fx(tmp_path, unsealed_s74=True))
    assert f"  s74  other  {_BASIS}  panel-s74-verdict dissent:LOSS" in lines
    line = next(ln for ln in lines if ln.startswith("  s74  "))
    assert "@" not in line, line
