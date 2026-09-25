"""s86 w2 pins — the ships-row suite gate, pinned from the other side.

Spec source: issue #13 (khursanirevo/rumpun#13) and the s86 w1 brief
(.rumpun/runs/s86/w1/prompt.md). Issue #13: the s80/s82 panel sweep
requests were refused pre-route because the gate read one cell of the
ships row; w1 lands the row-wide scan (the `suite N/N` search spans the
whole row, every cell). These pins hold the landed gate's row-wide
contract from the other side — the adversarial shapes, where a lenient
gate would fabricate and a strict one would go silent.

Contract these pins hold -- src/rumpun/panel.py claim_set, the
ships-row suite scan:

1. Claim in every cell: a row whose every content cell carries
   `suite N/N` composes. The suite the gate returns is the claimed
   numbers, verbatim — acceptance reads the row, it never invents.
2. Claim in no cell (the s81 shape, issue #13): the row carries no
   `suite N/N` anywhere, so the gate refuses — PanelError naming the
   season and the DESIGN.md path. Never a silent skip, never None.
3. Claim split across cells: `suite` in one cell and `12/12` in the
   next is NOT a claim — the cell boundary breaks it. The gate refuses
   with the same named message. A lenient implementation that joins
   the cells (or strips the pipes) would fabricate `suite 12/12` from
   fragments and accept; this pin locks that out. The named refusal is
   the never-silent half of the row-wide contract: acceptance requires
   a well-formed claim in the row as written.

Offline: every pin is in-process over a tmp_path fixture campaign (the
s80w2 layout: season yaml inside the root, DESIGN.md beside the
campaign, the harvest record sealed through akar itself into the
fixture-local ledger). claim_set is pure file reading — no route call,
no gh, no network; the route seam is never constructed.

Measured 2026-09-17 against the landed row-wide scan (w1's panel.py in
tree, `_SUITE_RE.search(rows[-1])`): 3 passed. The verdicts are stable
across the cell-local → row-wide landing (every cell accepts both
ways; no cell and split refuse both ways), so these pins certify the
contract, not the diff.

Grafting: drop this file into tests/. All helpers and constants carry
the _s86w2_ prefix; nothing collides with existing defs.
Fixture-shape assumptions the harness reconciles at merge if the
landed shape differs:
(a) the refusal message stays
    `no `suite N/N` in <sid>'s ships row in <path>` — issue #13
    quotes it verbatim and w1's brief requires the same message on the
    nowhere shape;
(b) a split-across-cells claim is not a claim — the scan reads the row
    as written (no cell joining, no pipe stripping);
(c) the campaign layout is the s80w2 fixture layout claim_set already
    reads.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rumpun import akar

_S86W2_SEASON_YAML = (
    "goal: pin the ships-row suite gate's adversarial shapes\n"
    "methodology:\n"
    "  primary_change:\n"
    "    type: retune\n"
    '    expected_band: "WIN if the suite gate holds every adversarial shape"\n'
)

_S86W2_HARVEST_BODY = (
    "season {sid}: completed\n"
    "\n"
    "verdict: WIN\n"
    "implies: the ships-row suite gate holds every adversarial shape\n"
    "observed: the gate verdicts are explicit in both directions\n"
)


def _s86w2_panel_module():
    """Import rumpun.panel; fail naming the spec reason when unlanded."""
    try:
        from rumpun import panel as panel_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/panel.py missing/unimportable: {exc}")
    return panel_module


def _s86w2_campaign(tmp_path: Path, sid: str, ships_row: str) -> Path:
    """A fresh campaign: the s80w2 layout claim_set reads.

    <tmp>/s86w2proj/DESIGN.md beside <tmp>/s86w2proj/.rumpun/ with
    rumpun.yaml, seasons/<sid>.yaml, and the <sid>-harvest record
    sealed through akar itself (fixture-local ledger; the real ledger
    is never touched).
    """
    campaign = tmp_path / "s86w2proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text("autonomy:\n  stage: manual\n", encoding="utf-8")
    (root / "seasons" / f"{sid}.yaml").write_text(_S86W2_SEASON_YAML, encoding="utf-8")
    (campaign / "DESIGN.md").write_text(
        "| season | verdict | ships |\n|---|---|---|\n" + ships_row + "\n",
        encoding="utf-8",
    )
    akar.append_record(
        root, f"{sid}-harvest", f"season {sid} harvest", _S86W2_HARVEST_BODY.format(sid=sid)
    )
    return root


def test_s86w2_claim_in_every_cell_composes_and_reads_the_numbers(tmp_path: Path) -> None:
    """Shape 1: every content cell carries `suite N/N` — the gate composes.

    The suite the gate returns is the claimed numbers verbatim:
    acceptance reads the row; it never invents a count.
    """
    panel = _s86w2_panel_module()
    root = _s86w2_campaign(
        tmp_path,
        "s86a",
        "| s86a | WIN suite 12/12 | the pins suite 12/12 | suite 12/12 |",
    )
    claims = panel.claim_set(root, "s86a")
    assert claims.suite == "12/12"
    assert claims.repro is None  # no resolves: declared — the s70 render shape
    assert claims.implies  # the harvest evidence reached the claim set


def test_s86w2_claim_in_no_cell_refuses_with_the_named_message(tmp_path: Path) -> None:
    """Shape 2 (the s81 shape, issue #13): no `suite N/N` anywhere — refuse named.

    The refusal names the season and the DESIGN.md path; a silent skip
    (None, an empty suite, a pass-through) fails the pin.
    """
    panel = _s86w2_panel_module()
    root = _s86w2_campaign(
        tmp_path,
        "s86b",
        "| s86b | WIN (band clauses met) | landed clean | shipped | verified |",
    )
    design_path = root.parent / "DESIGN.md"
    with pytest.raises(panel.PanelError) as excinfo:
        panel.claim_set(root, "s86b")
    assert str(excinfo.value) == (
        f"no `suite N/N` in s86b's ships row in {design_path}"
    )


def test_s86w2_claim_split_across_cells_is_not_a_claim(tmp_path: Path) -> None:
    """Shape 3: `suite` and `12/12` in adjacent cells refuse, same named message.

    The cell boundary breaks the claim: the row as written carries no
    well-formed `suite N/N`. A lenient gate that joins the cells (or
    strips the pipes) would fabricate the claim and accept — this pin
    locks that out; the refusal is the never-silent half of the
    row-wide contract.
    """
    panel = _s86w2_panel_module()
    root = _s86w2_campaign(
        tmp_path,
        "s86c",
        "| s86c | WIN (band clauses met) | suite | 12/12 | landed |",
    )
    design_path = root.parent / "DESIGN.md"
    with pytest.raises(panel.PanelError) as excinfo:
        panel.claim_set(root, "s86c")
    assert str(excinfo.value) == (
        f"no `suite N/N` in s86c's ships row in {design_path}"
    )
