"""s75 w2 pins — the panel gets teeth: a non-WIN verdict cards on the board.

Spec source: .rumpun/runs/s75/w2/prompt.md (the s75 w2 brief); the s73
panel pins are the record-shape precedent, the s69 board pins are the
kanban-render/degradation precedent. Offline: these pins make no route
call and no gh call -- panel records are hand-sealed through akar, with
bodies mirroring request_review's real shapes.

Contract these pins hold -- src/rumpun/panel.py + src/rumpun/kanban.py:

1. panel.latest_panel(root, sid): the newest panel-<sid>* record's
   status line, None when none. Newest follows the akar recovery
   convention -- the outcome record (panel-<sid>-verdict, else
   panel-<sid>-error) supersedes the pending panel-<sid> -- and the
   trailing dash keeps s7 from reading s70's records. A panel-family
   record without a status line is a PanelError, never a silent skip.
2. kanban._panel_cards via kanban.render: for the newest CLOSED season
   (harvested) whose newest panel status is not a WIN verdict, exactly
   one NEED HUMAN card with the seq 8 four sentences, citing the record
   id. WIN verdicts (bare or reasoned) and panel-less seasons never
   card; the scan walks past them to older closed seasons. A pending
   panel (request or error record) is non-WIN and cards.
3. Degradation holds: with board.pickup raising, render still renders
   the local columns and the panel card (the s69 seam stays green).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)


def _s75w2_repo_root() -> Path:
    """Repo root from this file's location (the s70/s71 walk-up rule)."""
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s75w2_modules():
    """Import rumpun.panel + rumpun.kanban; fail naming the spec reason."""
    try:
        from rumpun import kanban, panel
    except ImportError as exc:
        pytest.fail(f"src/rumpun panel.py/kanban.py missing/unimportable: {exc}")
    return panel, kanban


def _s75w2_campaign(tmp_path: Path, name: str = "s75w2proj") -> Path:
    """A fresh .rumpun root: no budget cap, no audits, no directives."""
    campaign = tmp_path / name
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text("autonomy:\n  stage: manual\n", encoding="utf-8")
    return root


def _s75w2_seal(root: Path, rid: str, title: str, body: str) -> Path:
    """Hand-seal one record through akar (the fixture discipline)."""
    from rumpun import akar

    return akar.append_record(root, rid, title, body)


def _s75w2_harvest(root: Path, sid: str, verdict: str = "WIN") -> None:
    _s75w2_seal(
        root,
        f"{sid}-harvest",
        f"season {sid} harvest",
        f"season {sid}: completed\nverdict: {verdict}\nimplies: fixture only\n",
    )


def _s75w2_pending(root: Path, sid: str) -> None:
    _s75w2_seal(
        root,
        f"panel-{sid}",
        f"panel review request {sid} (pending)",
        "status: pending\n"
        "route: gpt-6-astra (bounded 300s); the outcome seals as"
        " panel-<sid>-verdict or -error\n"
        "review request:\n"
        f"panel review request: {sid}\n"
        "verdict: pending (the second-opinion route answers next season)\n",
    )


def _s75w2_verdict(root: Path, sid: str, status: str) -> None:
    _s75w2_seal(
        root,
        f"panel-{sid}-verdict",
        f"panel verdict {sid} ({status})",
        f"status: {status}\n"
        "route: gpt-6-astra (bounded 300s)\n"
        "reply:\n"
        f"second opinion\nverdict: {status}\nend of reply\n",
    )


def _s75w2_error(root: Path, sid: str) -> None:
    _s75w2_seal(
        root,
        f"panel-{sid}-error",
        f"panel route error {sid} (pending)",
        "status: pending\n"
        "route: gpt-6-astra (bounded 300s)\n"
        "error:\n"
        "gpt-6-astra route timed out after 300s (the call was killed)\n",
    )


def _s75w2_patch_pickup(
    monkeypatch: pytest.MonkeyPatch,
    rows: list[dict[str, str]] | None = None,
    raise_: bool = False,
) -> None:
    """Patch both seam names (the s69 'either import style lands' rule)."""
    from rumpun import board, kanban

    def seam(*args: object, **kwargs: object) -> list[dict[str, str]]:
        if raise_:
            raise RuntimeError("s75w2: board pickup exploded")
        return list(rows or [])

    monkeypatch.setattr(board, "pickup", seam)
    if hasattr(kanban, "pickup"):
        monkeypatch.setattr(kanban, "pickup", seam)


def test_s75w2_latest_panel_reads_verdict_over_pending(tmp_path: Path) -> None:
    """The outcome record supersedes the pending record it carries."""
    panel, _ = _s75w2_modules()
    root = _s75w2_campaign(tmp_path)
    _s75w2_pending(root, "s801")
    _s75w2_verdict(root, "s801", "WIN the band holds")
    assert panel.latest_panel(root, "s801") == "WIN the band holds", (
        "the verdict record must win over the pending record"
    )


def test_s75w2_latest_panel_loss_pending_error_none(tmp_path: Path) -> None:
    """LOSS reads off a verdict record; pending off request or error."""
    panel, _ = _s75w2_modules()
    root = _s75w2_campaign(tmp_path)
    assert panel.latest_panel(root, "s801") is None, "no records: not None"
    _s75w2_pending(root, "s801")
    assert panel.latest_panel(root, "s801") == "pending", "request-only: not pending"
    _s75w2_verdict(root, "s801", "LOSS the band slipped")
    assert panel.latest_panel(root, "s801") == "LOSS the band slipped"
    root_err = _s75w2_campaign(tmp_path, name="s75w2err")
    _s75w2_pending(root_err, "s801")
    _s75w2_error(root_err, "s801")
    assert panel.latest_panel(root_err, "s801") == "pending", (
        "the error record stays status pending"
    )


def test_s75w2_latest_panel_season_prefix_is_exact(tmp_path: Path) -> None:
    """The trailing dash keeps neighbor ids apart: s8 never reads s80's."""
    panel, _ = _s75w2_modules()
    root = _s75w2_campaign(tmp_path)
    _s75w2_pending(root, "s80")
    _s75w2_verdict(root, "s80", "WIN")
    assert panel.latest_panel(root, "s8") is None, "prefix leak: s8 read s80"
    assert panel.latest_panel(root, "s801") is None, "prefix leak: s801 read s80"
    assert panel.latest_panel(root, "s80") == "WIN"


def test_s75w2_latest_panel_refuses_statusless_record(tmp_path: Path) -> None:
    """A panel-family record without a status line is a loud PanelError."""
    panel, _ = _s75w2_modules()
    root = _s75w2_campaign(tmp_path)
    _s75w2_seal(root, "panel-s801", "hand-made, statusless", "no status here\n")
    with pytest.raises(panel.PanelError, match="panel-s801"):
        panel.latest_panel(root, "s801")


def test_s75w2_non_win_verdict_cards_once_with_four_sentences(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A LOSS verdict: exactly one card, four sentences, record id cited."""
    _, kanban = _s75w2_modules()
    root = _s75w2_campaign(tmp_path)
    _s75w2_harvest(root, "s801", verdict="LOSS")
    _s75w2_pending(root, "s801")
    _s75w2_verdict(root, "s801", "LOSS the band slipped")
    _s75w2_patch_pickup(monkeypatch)
    cards = kanban._panel_cards(root)
    assert len(cards) == 5, f"title plus four sentences expected: {cards!r}"
    assert cards[0] == (
        "- panel verdict s801: LOSS the band slipped  [panel-s801-verdict]"
    ), f"the title must carry the status and cite the record id: {cards[0]!r}"
    assert cards[1].startswith(
        "    what happened: the panel's second opinion on s801 sealed"
    ), cards[1]
    assert "status: LOSS the band slipped." in cards[1], cards[1]
    assert cards[2].startswith("    what needs doing: read panel-s801-verdict"), cards[2]
    assert cards[3].startswith("    why it needs a human:"), cards[3]
    assert cards[4].startswith("    what happens if nobody acts:"), cards[4]
    rendered = kanban.render(root)
    need_at = rendered.index("NEED HUMAN")
    done_at = rendered.index("\nDONE ")
    card_at = rendered.index("- panel verdict s801:")
    assert need_at < card_at < done_at, "the card is not in the NEED HUMAN column"


def test_s75w2_win_verdict_renders_no_card(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WIN cards nothing -- a reasoned 'WIN ...' status is still a WIN."""
    _, kanban = _s75w2_modules()
    root = _s75w2_campaign(tmp_path)
    _s75w2_harvest(root, "s801")
    _s75w2_verdict(root, "s801", "WIN the band holds")
    _s75w2_patch_pickup(monkeypatch)
    assert kanban._panel_cards(root) == [], "a WIN verdict must not card"
    rendered = kanban.render(root)
    assert "panel verdict" not in rendered, "a WIN verdict leaked a card"


def test_s75w2_newest_non_win_cards_past_quiet_seasons(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The scan walks past quiet seasons to the newest non-WIN verdict.

    s801 has no panel records; s802's panel said WIN (its LOSS harvest
    verdict is the DONE column's business, not a panel card); s803's
    panel said LOSS -- exactly that season cards. A pending-only panel
    is non-WIN too and cards as pending.
    """
    _, kanban = _s75w2_modules()
    root = _s75w2_campaign(tmp_path)
    _s75w2_harvest(root, "s801")
    _s75w2_harvest(root, "s802", verdict="LOSS")
    _s75w2_verdict(root, "s802", "WIN")
    _s75w2_harvest(root, "s803")
    _s75w2_verdict(root, "s803", "LOSS the band slipped")
    _s75w2_patch_pickup(monkeypatch)
    cards = kanban._panel_cards(root)
    assert len(cards) == 5, f"exactly one card expected: {cards!r}"
    assert cards[0] == "- panel verdict s803: LOSS the band slipped  [panel-s803-verdict]"
    pending_root = _s75w2_campaign(tmp_path, name="s75w2pending")
    _s75w2_harvest(pending_root, "s804")
    _s75w2_pending(pending_root, "s804")
    pending_cards = kanban._panel_cards(pending_root)
    assert pending_cards[0] == "- panel verdict s804: pending  [panel-s804]", (
        f"a pending panel must card as pending: {pending_cards!r}"
    )


def test_s75w2_pickup_raise_degrades_with_the_panel_card_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The s69 seam holds: a pickup raise degrades, the panel card stays."""
    _, kanban = _s75w2_modules()
    root = _s75w2_campaign(tmp_path)
    _s75w2_harvest(root, "s801")
    _s75w2_verdict(root, "s801", "INVALID the seal broke")
    _s75w2_patch_pickup(monkeypatch, raise_=True)
    rendered = kanban.render(root)
    assert "- panel verdict s801: INVALID the seal broke  [panel-s801-verdict]" in rendered
    assert "campaign_cost_cap is unset" in rendered, "the local NEED HUMAN card dropped"
