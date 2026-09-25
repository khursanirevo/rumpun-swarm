"""s70 w2 pins — the audit panel's input contract (seeded issue #1).

Directive seq 0 surface: the input the panel reviews plus the dry-run
and pending-record surfaces; the second-opinion route itself lands next
season and no pin calls it. Spec source: .rumpun/runs/s70/w2/prompt.md;
ledger anchor s69-harvest; the s69 w2 file is the fixture-pattern
precedent. Assumptions the harness reconciles at merge:
.rumpun/runs/s70/w2/notes.md.

Contract these pins hold — src/rumpun/panel.py, importable as
rumpun.panel:

1. claim_set(root, sid) reads the REAL s69 files inside a fixture
   campaign (copies of .rumpun/seasons/s69.yaml, the real s69-harvest
   ledger record, and the real DESIGN.md beside the campaign root) and
   returns exactly the season's goal, expected_band, implies/observed
   lines, and the DESIGN ships-row suite count 303/303. Pure file
   reading; no network.
2. render_review(claims) is deterministic (same claims -> same bytes)
   and bounded to one screen: at most MAX_REVIEW_LINES lines, none
   wider than MAX_LINE_CHARS; long values clip with an ellipsis and
   evidence lines past the budget are elided behind a counting marker
   inside the same bound.
3. request_review(root, sid, dry_run=False) appends the sha-sealed
   `panel-s69` akar record: header, `status: pending` first in the
   body, the rendered review inside the body, the recomputed body
   sha256 matching the seal line, and a second run refusing (ledger
   append-only, ids unique).
4. --dry-run returns the rendered review and writes nothing: no
   ledger file, no record id.
5. The CLI surface: `rumpun audit --panel <sid> [--dry-run]` parses
   and dispatches to cmd_audit (the wiring pin; no subprocess).

Fixture discipline: the fixture campaign copies the real s69 artifacts,
so the pin reads sealed campaign history, not synthetic strings; the
DESIGN.md copy is the live one (the s69 ships row is stable history).

Measured (two solo runs, /tmp/s70w2-pins-run{1,2}.log, 2026-09-17): all
five pins PASS both runs (rc=0, 5 passed in ~1s each). No reds to
reconcile: the module landed inside this lane before the pins ran.
ruff --no-respect-gitignore clean on panel.py, cli.py, and this file
after the SIM300 fix (the run1 finding). E2E: `rumpun audit --panel
s69 --dry-run` against the real campaign printed the bounded review,
exit 0, and the real ledger stayed untouched (grep for panel-s69
finds no record).
"""


from __future__ import annotations

import hashlib
import logging
import shutil
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)


def _s70w2_repo_root() -> Path:
    """Repo root from this file's location, workspace and merged alike.

    parents[] walk-up requires pyproject.toml, src/rumpun/report.py and
    DESIGN.md together, so archived src/ copies in scratch trees never
    match (the s27 walk-up helper's rule, s69 w2's precedent). Merge
    reconciliation (s70 close): the checker's archive extract carries
    the committed campaign files but no .venv, so the locator keys on
    the campaign's own DESIGN.md instead - both environments match.
    """
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s70w2_panel_module():
    """Import rumpun.panel; fail naming the spec reason when unlanded."""
    try:
        from rumpun import panel as panel_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/panel.py missing/unimportable: {exc}")
    return panel_module


def _s70w2_fixture_campaign(tmp_path: Path) -> Path:
    """A fixture campaign carrying the REAL s69 panel input files.

    Layout: <tmp>/s70w2proj/DESIGN.md (the live DESIGN.md copy) beside
    <tmp>/s70w2proj/.rumpun/ with rumpun.yaml, the real seasons/s69.yaml,
    and the real s69-harvest ledger record resolved through akar (the
    discipline, not a filename glob).
    """
    repo_root = _s70w2_repo_root()
    campaign = tmp_path / "s70w2proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        "autonomy:\n  stage: manual\n", encoding="utf-8"
    )
    shutil.copyfile(repo_root / "DESIGN.md", campaign / "DESIGN.md")
    shutil.copyfile(repo_root / ".rumpun" / "seasons" / "s69.yaml", root / "seasons" / "s69.yaml")
    from rumpun import akar

    harvest_src = akar.find_record(repo_root / ".rumpun", "s69-harvest")
    shutil.copyfile(harvest_src, root / "ledger" / harvest_src.name)
    return root


def test_s70w2_claim_set_reads_the_real_s69_files(tmp_path: Path) -> None:
    """Pin the claim set off the real s69 yaml, harvest record, DESIGN row."""
    panel = _s70w2_panel_module()
    root = _s70w2_fixture_campaign(tmp_path)
    claims = panel.claim_set(root, "s69")
    assert claims.sid == "s69"
    assert claims.goal.startswith("rumpun gains a cross-machine surface"), (
        f"goal not read off the real s69.yaml: {claims.goal[:80]!r}"
    )
    assert claims.expected_band.startswith("WIN if khursanirevo/rumpun exists"), (
        f"expected_band not read off the real s69.yaml: {claims.expected_band[:80]!r}"
    )
    assert len(claims.implies) == 1 and claims.implies[0].startswith(
        "implies: the cross-machine surface is three quarters landed"
    ), f"implies lines not read off the real s69-harvest record: {claims.implies!r}"
    assert claims.observed == (), f"unexpected observed lines: {claims.observed!r}"
    assert claims.suite == "303/303", (
        f"suite count not read off the real DESIGN.md ships row: {claims.suite!r}"
    )


def test_s70w2_render_review_stable_and_bounded() -> None:
    """Same claims -> same bytes; one screen; clip and elision markers."""
    panel = _s70w2_panel_module()
    claims = panel.ClaimSet(
        sid="s70w2syn",
        goal="g" * 500,
        expected_band="WIN if " + "b" * 500,
        implies=tuple(f"implies: evidence line {i} " + "e" * 90 for i in range(30)),
        observed=tuple(f"observed: fact {j} " + "o" * 60 for j in range(5)),
        suite="999/999",
    )
    text = panel.render_review(claims)
    assert text == panel.render_review(claims), "render_review is not deterministic"
    lines = text.splitlines()
    assert len(lines) <= panel.MAX_REVIEW_LINES, (
        f"review is {len(lines)} lines, over the {panel.MAX_REVIEW_LINES}-line bound"
    )
    over = [ln for ln in lines if len(ln) > panel.MAX_LINE_CHARS]
    assert not over, f"lines over the {panel.MAX_LINE_CHARS}-char bound: {over[:3]}"
    assert lines[0] == "panel review request: s70w2syn"
    assert lines[1] == "goal: " + "g" * 91 + "...", f"goal not clipped: {lines[1]!r}"
    assert lines[-1] == "verdict: pending (the second-opinion route answers next season)"
    elision = [ln for ln in lines if ln.startswith("(+") and ln.endswith(" elided)")]
    assert len(elision) == 1, f"expected exactly one elision marker: {elision!r}"
    assert any(ln == "suite: 999/999" for ln in lines), "suite line missing"


def test_s70w2_pending_record_seals(tmp_path: Path) -> None:
    """The pending record lands through akar: header, body, seal.

    The s108 rerun convention retires the s79 refusal: a second run
    derives panel-s69-2 and the first record stays byte-identical.
    """
    panel = _s70w2_panel_module()
    root = _s70w2_fixture_campaign(tmp_path)
    from rumpun import akar

    panel.request_review(root, "s69", dry_run=False)
    record = akar.find_record(root, "panel-s69")
    text = record.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines[0] == "# akar record: panel-s69"
    assert lines[1] == "id: panel-s69"
    assert lines[4] == "status: pending", f"body does not open pending: {lines[4]!r}"
    body = "\n".join(lines[4:-1])
    seal = "sha256: " + hashlib.sha256(body.encode("utf-8")).hexdigest()
    assert lines[-1] == seal, (
        f"seal mismatch: claimed {lines[-1]!r} recomputed {seal!r} (the akar "
        f"discipline is not holding the record)"
    )
    review = panel.render_review(panel.claim_set(root, "s69"))
    assert review in body, "the rendered review is not inside the sealed body"
    panel.request_review(root, "s69", dry_run=False)
    second = akar.find_record(root, "panel-s69-2")
    assert second.read_text(encoding="utf-8").splitlines()[1] == "id: panel-s69-2", (
        "the rerun did not land the derived second id"
    )
    assert akar.find_record(root, "panel-s69").read_text(encoding="utf-8") == text, (
        "the rerun rewrote the first record; the ledger never rewrites"
    )


def test_s70w2_dry_run_writes_nothing(tmp_path: Path) -> None:
    """--dry-run returns the rendered review; the ledger stays untouched."""
    panel = _s70w2_panel_module()
    root = _s70w2_fixture_campaign(tmp_path)
    from rumpun import akar

    ledger_before = sorted(p.name for p in (root / "ledger").iterdir())
    review = panel.request_review(root, "s69", dry_run=True)
    assert review == panel.render_review(panel.claim_set(root, "s69")), (
        "dry run did not return the rendered review"
    )
    ledger_after = sorted(p.name for p in (root / "ledger").iterdir())
    assert ledger_after == ledger_before, (
        f"dry run wrote to the ledger: {set(ledger_after) - set(ledger_before)!r}"
    )
    assert "panel-s69" not in akar.declared_ids(root), (
        "dry run appended a panel-s69 record"
    )


def test_s70w2_audit_parser_wires_panel_flags() -> None:
    """`rumpun audit --panel <sid> [--dry-run]` parses and dispatches."""
    from rumpun import cli

    args = cli.build_parser().parse_args(["audit", "--panel", "s69", "--dry-run"])
    assert args.panel == "s69"
    assert args.dry_run is True
    assert args.func is cli.cmd_audit
    args_no_dry = cli.build_parser().parse_args(["audit", "--panel", "s69"])
    assert args_no_dry.panel == "s69"
    assert args_no_dry.dry_run is False
