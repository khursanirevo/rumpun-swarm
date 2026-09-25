"""s80 w2 pins — the repro-backed closure contract's checkable surface.

Spec sources: .rumpun/runs/s80/w2/prompt.md; issue #5
(khursanirevo/rumpun#5, the audit-43 epistemics residual -- it stays
OPEN; the contract is a standing standard, not a fix); the contract
text at .rumpun/plugins/kancil-base-draft/priors/templates/
repro-backed-closure.md. Precedents: the s70 w2 pins (the panel-input
fixture discipline, the bounded-render pins), the s79 w2 pins (the
repro-shaped pin, the campaign fixture builder, the write-nothing
snapshot).

Offline: these pins make no gh call; claim_set scans fixture trees
only.

Contract these pins hold -- src/rumpun/panel.py claim_set/render_review
(the s80 w2 repro-backed closure extension):

1. A fixture season whose yaml declares `resolves: 5` and whose pins
   tree carries the repro test (name = repro + issue<N>) gets
   `repro: present tests/<file>::<test>` in the claim set and in the
   rendered review: deterministic, inside the one-screen bound, and
   claim_set writes nothing.
2. The same season WITHOUT the repro test is flagged, not errored:
   claim_set succeeds and the review carries the exact line
   `repro: absent`.
3. A season with no `resolves:` renders the pre-s80 shape: no repro
   line anywhere in the review.
4. A present-but-unparseable `resolves:` is a PanelError naming the
   season yaml -- a declaration the panel cannot read is worse than no
   declaration.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from rumpun import akar

logger = logging.getLogger(__name__)

S80W2_SID = "s80f"
S80W2_ISSUE5_URL = "https://github.com/khursanirevo/rumpun/issues/5"

S80W2_SEASON_YAML = """\
id: s80f
parent: s80
goal: fixture season for the s80 w2 repro-backed-closure pins
metric: modules_integrated
resolves: 5
methodology:
  primary_change:
    type: retune
    expected_band: "WIN if the issue #5 repro is red before and green after"
"""

S80W2_DESIGN_ROW = (
    "| season | verdict | ships |\n"
    "|---|---|---|\n"
    "| s80f | WIN (band clauses met) | the repro-backed closure pins; suite 4/4 |\n"
)

S80W2_HARVEST_BODY = (
    "season s80f: completed\n"
    "duration: 60s\n"
    "\n"
    "| agent | route | state | exit_code | seconds |\n"
    "|---|---|---|---|---|\n"
    "| w1 | fable | exited | 0 | 60.0 |\n"
    "\n"
    "verdict: WIN\n"
    "implies: issue #5 repro red-before/green-after: test_s80f_issue5_repro_green\n"
    "observed: the repro resolves offline\n"
)

S80W2_REPRO_TESTS = (
    "def test_s80f_issue5_repro_green():\n"
    '    """repro: khursanirevo/rumpun#5 -- red before the fix, green after."""\n'
    "\n"
    "    assert True\n"
)


def _s80w2_panel_module():
    """Import rumpun.panel; fail naming the spec reason when unlanded."""
    try:
        from rumpun import panel as panel_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/panel.py missing/unimportable: {exc}")
    return panel_module


def _s80w2_campaign(tmp_path: Path, season_yaml: str) -> Path:
    """A fresh campaign: .rumpun root, the fixture season, a DESIGN ships row.

    Layout: <tmp>/s80w2proj/DESIGN.md beside <tmp>/s80w2proj/.rumpun/
    with rumpun.yaml and seasons/s80f.yaml -- the layout claim_set reads
    (the season yaml inside the root, DESIGN.md beside the campaign).
    """
    campaign = tmp_path / "s80w2proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text("autonomy:\n  stage: manual\n", encoding="utf-8")
    (root / "seasons" / f"{S80W2_SID}.yaml").write_text(season_yaml, encoding="utf-8")
    (campaign / "DESIGN.md").write_text(S80W2_DESIGN_ROW, encoding="utf-8")
    return root


def _s80w2_sealed_harvest(root: Path) -> Path:
    """Append the s80f-harvest record through akar itself, so the seal is real."""
    return akar.append_record(
        root, f"{S80W2_SID}-harvest", f"season {S80W2_SID} harvest", S80W2_HARVEST_BODY
    )


def _s80w2_repro_tests(root: Path) -> None:
    """The season's pins tree: tests/test_s80f_pins.py with the repro test."""
    tests_dir = root.parent / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_s80f_pins.py").write_text(S80W2_REPRO_TESTS, encoding="utf-8")


def _s80w2_tree_bytes(base: Path) -> dict[str, bytes]:
    """Every file under base as {relative path: bytes}, for write-nothing pins."""
    return {
        str(path.relative_to(base)): path.read_bytes()
        for path in sorted(base.rglob("*"))
        if path.is_file()
    }


def test_s80w2_repro_backed_season_carries_present_line(tmp_path: Path) -> None:
    """The contract met: `repro: present <file>::<test>` in claim and review.

    The fixture season declares `resolves: 5`; the pins tree carries
    test_s80f_issue5_repro_green. claim_set names it; the rendered
    review carries the repro line inside the fixed block; the render is
    deterministic and bounded; claim_set writes nothing.
    """
    panel = _s80w2_panel_module()
    root = _s80w2_campaign(tmp_path, S80W2_SEASON_YAML)
    _s80w2_sealed_harvest(root)
    _s80w2_repro_tests(root)
    before = _s80w2_tree_bytes(root.parent)
    claims = panel.claim_set(root, S80W2_SID)
    expected = "present tests/test_s80f_pins.py::test_s80f_issue5_repro_green"
    assert claims.repro == expected, f"claim set repro: {claims.repro!r}"
    review = panel.render_review(claims)
    assert f"repro: {expected}" in review.splitlines(), f"review:\n{review}"
    assert review == panel.render_review(claims), "render_review not deterministic"
    assert len(review.splitlines()) <= panel.MAX_REVIEW_LINES, "review over the bound"
    assert all(len(ln) <= panel.MAX_LINE_CHARS for ln in review.splitlines())
    assert _s80w2_tree_bytes(root.parent) == before, "claim_set wrote files"


def test_s80w2_defect_season_without_repro_is_flagged_absent(tmp_path: Path) -> None:
    """The contract broken: claim_set succeeds; the review says `repro: absent`.

    The flag, not an error: the panel weighs the absence against the
    closure claim; the fact is not the judgment.
    """
    panel = _s80w2_panel_module()
    root = _s80w2_campaign(tmp_path, S80W2_SEASON_YAML)
    _s80w2_sealed_harvest(root)
    claims = panel.claim_set(root, S80W2_SID)
    assert claims.repro == "absent", f"claim set repro: {claims.repro!r}"
    review = panel.render_review(claims)
    assert "repro: absent" in review.splitlines(), f"review:\n{review}"


def test_s80w2_season_without_resolves_keeps_the_s70_render(tmp_path: Path) -> None:
    """Backward compat: no `resolves:` -> no repro line, the s70 shape."""
    panel = _s80w2_panel_module()
    yaml_text = S80W2_SEASON_YAML.replace("resolves: 5\n", "")
    root = _s80w2_campaign(tmp_path, yaml_text)
    _s80w2_sealed_harvest(root)
    claims = panel.claim_set(root, S80W2_SID)
    assert claims.repro is None, f"repro should be unset: {claims.repro!r}"
    review = panel.render_review(claims)
    assert not any(ln.startswith("repro:") for ln in review.splitlines()), review


def test_s80w2_unparseable_resolves_is_a_panel_error(tmp_path: Path) -> None:
    """A present-but-unreadable `resolves:` refuses, naming the yaml."""
    panel = _s80w2_panel_module()
    yaml_text = S80W2_SEASON_YAML.replace(
        "resolves: 5", "resolves: someday, the right one"
    )
    root = _s80w2_campaign(tmp_path, yaml_text)
    _s80w2_sealed_harvest(root)
    with pytest.raises(panel.PanelError) as excinfo:
        panel.claim_set(root, S80W2_SID)
    message = str(excinfo.value)
    assert f"{root / 'seasons' / f'{S80W2_SID}.yaml'}" in message, message
    assert "resolves" in message, message
