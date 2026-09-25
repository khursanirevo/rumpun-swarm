"""s86 w1 pins — the panel suite gate reads the whole ships row (issue #13).

Spec sources: .rumpun/runs/s86/w1/prompt.md; issue #13
(khursanirevo/rumpun#13): the suite-claim scan took the third cell of
the ships row and searched only that cell, refusing s80/s82 whose
`suite N/N` sits in the verdict cell; the row is the surface. The s81
row carries the claim nowhere, so its refusal is correct and stays.

Precedents: the s70 w2 claim_set pins (the real campaign files beside a
fixture campaign, scratch-guarded repo locator) and the s84 w1 pins
(offline, hand-built fixture records).

Offline: pure file reading. claim_set runs over the real s80/s81/s82
rows (copied from the live DESIGN.md, stable history) and synthetic
rows for each cell placement. No route call, no gh call, no ledger
writes: fixtures hand-build the season yaml and harvest record (the
s84 rule: the harvest verb appends to the real ledger, so it is never
called from a fixture).
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

# The three real ships rows drive three pins each: s80 and s82 claim
# `suite N/N` from the VERDICT cell (the second), s81 nowhere (the
# refusal those two pins exist to contrast). Values from DESIGN.md at
# fix time; the real campaign copies the live DESIGN.md, so the pins
# track the stable-history rows themselves.
REAL_SIDS = ("s80", "s81", "s82")
S80_SUITE = "385/385"
S82_SUITE = "391/391"

# Hand-built season input, the claim_set contract minimum.
SEASON_YAML = (
    "goal: the suite gate scans every cell of the ships row\n"
    "methodology:\n"
    "  primary_change:\n"
    "    expected_band: WIN if the gate passes every cell placement\n"
)


def _s86w1_record(sid: str) -> str:
    """One hand-built harvest record, the akar layout minus date/sha."""
    return (
        f"# akar record: {sid}-harvest\n"
        f"id: {sid}-harvest\n"
        "title: the season landed\n"
        "implies: the suite gate scans every cell of the ships row\n"
        "observed: the gate refused three of five sweep requests on one cell\n"
    )


def _s86w1_repo_root() -> Path:
    """Repo root from this file's location, workspace and merged alike.

    The s70 w2 locator: the walk-up keys on pyproject.toml,
    src/rumpun/report.py, and DESIGN.md together, so archived src/
    copies in scratch trees never match, and the campaign's own
    DESIGN.md satisfies merge-reconciled checkers.
    """
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s86w1_panel_module():
    """Import rumpun.panel; fail naming the spec reason when unlanded."""
    try:
        from rumpun import panel as panel_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/panel.py missing/unimportable: {exc}")
    return panel_module


def _s86w1_campaign_root(tmp_path: Path, name: str) -> Path:
    """The campaign skeleton: .rumpun/{seasons,ledger,runs} + rumpun.yaml."""
    root = tmp_path / name / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text("autonomy:\n  stage: manual\n", encoding="utf-8")
    return root


def _s86w1_real_campaign(tmp_path: Path) -> Path:
    """The REAL s80/s81/s82 panel inputs beside a fixture campaign.

    Live DESIGN.md (the rows are stable history), the three real season
    yamls, and the three real harvest records resolved through akar
    (the discipline, not a filename glob) — the s70 shape.
    """
    repo_root = _s86w1_repo_root()
    root = _s86w1_campaign_root(tmp_path, "s86w1real")
    shutil.copyfile(repo_root / "DESIGN.md", root.parent / "DESIGN.md")
    from rumpun import akar

    for sid in REAL_SIDS:
        shutil.copyfile(
            repo_root / ".rumpun" / "seasons" / f"{sid}.yaml",
            root / "seasons" / f"{sid}.yaml",
        )
        harvest_src = akar.find_record(repo_root / ".rumpun", f"{sid}-harvest")
        shutil.copyfile(harvest_src, root / "ledger" / harvest_src.name)
    return root


def _s86w1_synth_campaign(tmp_path: Path, sid: str, row: str) -> Path:
    """One synthetic season: hand-built yaml + record under a fixture row."""
    root = _s86w1_campaign_root(tmp_path, f"s86w1synth-{sid}")
    (root.parent / "DESIGN.md").write_text(row + "\n", encoding="utf-8")
    (root / "seasons" / f"{sid}.yaml").write_text(SEASON_YAML, encoding="utf-8")
    (root / "ledger" / f"{sid}-harvest.md").write_text(
        _s86w1_record(sid), encoding="utf-8"
    )
    return root


def test_s86w1_real_s80_verdict_cell_claim_passes(tmp_path: Path) -> None:
    """The real s80 row claims `suite 385/385` from the verdict cell; in."""
    panel = _s86w1_panel_module()
    root = _s86w1_real_campaign(tmp_path)
    claims = panel.claim_set(root, "s80")
    assert claims.suite == S80_SUITE, (
        f"verdict-cell claim not read off the real s80 row: {claims.suite!r}"
    )
    assert claims.sid == "s80"
    assert claims.goal, "goal not read off the real s80.yaml"


def test_s86w1_real_s82_verdict_cell_claim_passes(tmp_path: Path) -> None:
    """The real s82 row claims `suite 391/391` from the verdict cell; in."""
    panel = _s86w1_panel_module()
    root = _s86w1_real_campaign(tmp_path)
    claims = panel.claim_set(root, "s82")
    assert claims.suite == S82_SUITE, (
        f"verdict-cell claim not read off the real s82 row: {claims.suite!r}"
    )


def test_s86w1_real_s81_nowhere_refuses_named_message(tmp_path: Path) -> None:
    """The real s81 row carries the claim nowhere; out, same message."""
    panel = _s86w1_panel_module()
    root = _s86w1_real_campaign(tmp_path)
    with pytest.raises(panel.PanelError, match=r"no `suite N/N` in s81's ships row"):
        panel.claim_set(root, "s81")


def test_s86w1_verdict_cell_claim_passes(tmp_path: Path) -> None:
    """A claim in the verdict cell (the second) satisfies the gate."""
    panel = _s86w1_panel_module()
    root = _s86w1_synth_campaign(
        tmp_path, "s90", "| s90 | WIN (band met, suite 12/12) | the evidence trail |"
    )
    claims = panel.claim_set(root, "s90")
    assert claims.suite == "12/12", (
        f"verdict-cell claim not read off the synthetic row: {claims.suite!r}"
    )


def test_s86w1_evidence_cell_claim_passes(tmp_path: Path) -> None:
    """A claim in the evidence cell (the third, the old code's only read) passes."""
    panel = _s86w1_panel_module()
    root = _s86w1_synth_campaign(
        tmp_path,
        "s91",
        "| s91 | WIN (band met) | the evidence trail, suite 13/13 |",
    )
    claims = panel.claim_set(root, "s91")
    assert claims.suite == "13/13", (
        f"evidence-cell claim not read off the synthetic row: {claims.suite!r}"
    )


def test_s86w1_both_cells_claim_leftmost_wins(tmp_path: Path) -> None:
    """Claims in both cells: the leftmost (verdict cell) claim is taken."""
    panel = _s86w1_panel_module()
    root = _s86w1_synth_campaign(
        tmp_path,
        "s92",
        "| s92 | WIN (band met, suite 14/14) | the evidence trail, suite 15/15 |",
    )
    claims = panel.claim_set(root, "s92")
    assert claims.suite == "14/14", (
        f"the leftmost claim is not the one taken: {claims.suite!r}"
    )


def test_s86w1_synth_nowhere_refuses_same_message(tmp_path: Path) -> None:
    """The s81 shape on a synthetic row: no claim anywhere, same refusal."""
    panel = _s86w1_panel_module()
    root = _s86w1_synth_campaign(
        tmp_path, "s93", "| s93 | WIN (band met) | the evidence trail |"
    )
    with pytest.raises(panel.PanelError, match=r"no `suite N/N` in s93's ships row"):
        panel.claim_set(root, "s93")
