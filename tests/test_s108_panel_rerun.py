"""s108 w1 pins - the panel rerun convention (the s79 refusal resolved).

s70 w2 sealed the refusal: a second real request_review run on the same
sid raised AkarError on the pending id. The s79 finding named that
refusal a defect: a rerun could never land, so a second-opinion answer
after a first answer was unrecordable. s108 w1 resolves it:
request_review derives the next free request id in the panel-<sid>
family (panel-<sid>, then panel-<sid>-2, -3, ...) and lands the rerun
beside the first request; the outcome seals under the derived id
(<derived>-verdict / <derived>-error). The ledger never rewrites: the
first request's records stay byte-identical.

Fixture: the s70 w2 pattern - the real s69 season yaml, the real
s69-harvest ledger record resolved through akar, the live DESIGN.md,
and a stubbed route. No network, no real route call.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest


def _repo_root() -> Path:
    """Repo root by the s70 w2 walk-up (pyproject + src/rumpun + DESIGN)."""
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _panel_module():
    """Import rumpun.panel; fail naming the spec reason when unlanded."""
    try:
        from rumpun import panel as panel_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/panel.py missing/unimportable: {exc}")
    return panel_module


def _fixture_campaign(tmp_path: Path) -> Path:
    """The s70 w2 fixture: real s69 panel-input files, no route calls."""
    repo_root = _repo_root()
    campaign = tmp_path / "s108w1proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text("autonomy:\n  stage: manual\n", encoding="utf-8")
    shutil.copyfile(repo_root / "DESIGN.md", campaign / "DESIGN.md")
    shutil.copyfile(
        repo_root / ".rumpun" / "seasons" / "s69.yaml", root / "seasons" / "s69.yaml"
    )
    from rumpun import akar

    harvest_src = akar.find_record(repo_root / ".rumpun", "s69-harvest")
    shutil.copyfile(harvest_src, root / "ledger" / harvest_src.name)
    return root


def _error_route(panel, message: str):
    """A route stub that always fails; the -error record is the outcome."""

    def route(root, review, timeout_s):
        raise panel.PanelError(message)

    return route


def _verdict_route(verdict: str):
    """A route stub that answers with one actionable verdict line."""

    def route(root, review, timeout_s):
        return f"verdict: {verdict}\nthe panel's reply body.\n"

    return route


def test_s108w1_second_run_lands_derived_request_id(tmp_path: Path) -> None:
    """Run 2 under the same sid lands panel-s69-2; run 1's bytes unchanged."""
    panel = _panel_module()
    root = _fixture_campaign(tmp_path)
    from rumpun import akar

    first_path = Path(
        panel.request_review(
            root, "s69", dry_run=False, route=_error_route(panel, "stub route down")
        )
    )
    first_bytes = first_path.read_bytes()
    second_path = Path(
        panel.request_review(
            root, "s69", dry_run=False, route=_error_route(panel, "stub route down")
        )
    )
    assert akar.find_record(root, "panel-s69") == first_path
    assert akar.find_record(root, "panel-s69-2") == second_path, (
        "the second run did not land under the derived id panel-s69-2"
    )
    assert first_path.read_bytes() == first_bytes, "run 2 rewrote run 1's record"
    second_text = second_path.read_text(encoding="utf-8")
    assert "status: pending" in second_text.splitlines(), (
        f"the rerun record does not open pending: {second_text.splitlines()[:6]}"
    )
    assert (
        "the outcome seals as panel-s69-2-verdict or panel-s69-2-error" in second_text
    ), "the rerun record does not name its own derived outcome ids"
    assert akar.find_record(root, "panel-s69-2-error"), (
        "the rerun outcome id did not derive"
    )


def test_s108w1_rerun_outcome_seals_under_derived_id(tmp_path: Path) -> None:
    """The rerun's outcome ids derive from the derived request id."""
    panel = _panel_module()
    root = _fixture_campaign(tmp_path)
    from rumpun import akar

    panel.request_review(root, "s69", dry_run=False, route=_verdict_route("WIN"))
    panel.request_review(
        root, "s69", dry_run=False, route=_error_route(panel, "stub route down")
    )
    verdict = akar.find_record(root, "panel-s69-verdict").read_text(encoding="utf-8")
    assert "status: WIN" in verdict.splitlines(), "gen-1 verdict record malformed"
    error = akar.find_record(root, "panel-s69-2-error").read_text(encoding="utf-8")
    assert "status: pending" in error.splitlines(), "rerun error record malformed"
    assert "stub route down" in error, "the error record does not quote the error"


def test_s108w1_latest_panel_surfaces_the_newest_generation(tmp_path: Path) -> None:
    """latest_panel_record prefers the highest rerun generation's outcome."""
    panel = _panel_module()
    root = _fixture_campaign(tmp_path)
    panel.request_review(root, "s69", dry_run=False, route=_verdict_route("WIN"))
    panel.request_review(root, "s69", dry_run=False, route=_verdict_route("LOSS"))
    assert panel.latest_panel_record(root, "s69") == ("panel-s69-2-verdict", "LOSS"), (
        "the family read did not surface the newest generation"
    )
    assert panel.latest_panel(root, "s69") == "LOSS", (
        "latest_panel did not answer from the newest generation"
    )


def test_s108w1_third_run_walks_the_free_ids(tmp_path: Path) -> None:
    """A third run derives panel-s69-3; earlier records stay byte-identical."""
    panel = _panel_module()
    root = _fixture_campaign(tmp_path)
    from rumpun import akar

    p1 = Path(
        panel.request_review(
            root, "s69", dry_run=False, route=_error_route(panel, "stub route down")
        )
    )
    p2 = Path(
        panel.request_review(
            root, "s69", dry_run=False, route=_error_route(panel, "stub route down")
        )
    )
    first_bytes = p1.read_bytes()
    second_bytes = p2.read_bytes()
    p3 = Path(
        panel.request_review(
            root, "s69", dry_run=False, route=_error_route(panel, "stub route down")
        )
    )
    assert akar.find_record(root, "panel-s69-3") == p3, (
        "the third run did not land under panel-s69-3"
    )
    assert p1.read_bytes() == first_bytes, "run 3 rewrote run 1's record"
    assert p2.read_bytes() == second_bytes, "run 3 rewrote run 2's record"


def test_s108w1_dry_run_still_writes_nothing(tmp_path: Path) -> None:
    """The dry-run contract holds after real runs; dry_run never appends."""
    panel = _panel_module()
    root = _fixture_campaign(tmp_path)
    from rumpun import akar

    panel.request_review(
        root, "s69", dry_run=False, route=_error_route(panel, "stub route down")
    )
    ledger_before = sorted(p.name for p in (root / "ledger").iterdir())
    review = panel.request_review(root, "s69", dry_run=True)
    assert review == panel.render_review(panel.claim_set(root, "s69")), (
        "dry run did not return the rendered review"
    )
    assert sorted(p.name for p in (root / "ledger").iterdir()) == ledger_before, (
        "dry run wrote to the ledger"
    )
    assert "panel-s69-2" not in akar.declared_ids(root), (
        "dry run appended a derived rerun record"
    )
