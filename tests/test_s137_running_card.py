"""s137 w1 pins: the index shows what is running right now.

Spec source: the s137 w1 brief. The index cards carry completed history
(fronts, lessons, spend, candidates) while the running season answers
only in a plain sentence. The index carries a running card: one cell
per season whose persisted state.json reads status "running", naming
the season id and its persisted started_at (the M1 contract: a
persisted read only, no clock, no /proc; a live elapsed never renders).
Honest shape: a running season -> the card names it; none -> the page
is byte-identical (byte-identical silence, the s129/s131/s132/s133
precedent). Fixture discipline: tmp campaigns, state files synthesized
per pin, no real writes.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-21 pre-implementation, /tmp/s137-w1-pins-red.txt.
- GREEN captured 2026-09-21 post-implementation, /tmp/s137-w1-pins-green.txt.
- The absence pins are green on both sides by design; the positive
  controls are the running-state pins in the same run.
"""

from __future__ import annotations

import json
from pathlib import Path

from rumpun import report


def _write_state(
    root: Path,
    sid: str,
    *,
    status: str,
    started_at: float,
    ended_at: float | None = None,
) -> None:
    """Synthesize the persisted season state exactly as the engine writes it."""
    season = root / "runs" / sid / "_season"
    season.mkdir(parents=True, exist_ok=True)
    state: dict[str, object] = {
        "id": sid,
        "status": status,
        "started_at": started_at,
        "agents": {},
    }
    if ended_at is not None:
        state["ended_at"] = ended_at
    (season / "state.json").write_text(json.dumps(state), encoding="utf-8")


def _proj(tmp_path: Path) -> Path:
    """Tmp campaign: the .rumpun skeleton plus one stopped season."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "seasons" / "s1.yaml").write_text(
        "id: s1\ngoal: fixture goal for s1\n", encoding="utf-8"
    )
    _write_state(root, "s1", status="stopped", started_at=1000.0, ended_at=1600.0)
    return root


def _render(root: Path, tmp_path: Path, name: str) -> str:
    return report.render_index(root, tmp_path / name).read_text(encoding="utf-8")


def _running_card(page: str) -> str:
    """The Running now card slice; fails by name when the card is absent."""
    start = page.find("<h2>Running now")
    assert start != -1, "the Running now card is missing"
    end = page.find("</section>", start)
    return page[start:end]


def test_s137rc_running_state_renders_card(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    _write_state(root, "s1", status="running", started_at=1000.0)
    page = _render(root, tmp_path, "i.html")
    card = _running_card(page)
    assert "<strong>s1</strong>" in card
    assert "1970-01-01T00:16:40+00:00" in card
    again = _render(root, tmp_path, "i2.html")
    assert page == again


def test_s137rc_no_running_state_byte_identical(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    a = _render(root, tmp_path, "ia.html")
    body = _render(root, tmp_path, "ib.html")
    assert a == body
    assert "Running now" not in a


def test_s137rc_completed_season_no_card(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    _write_state(root, "s1", status="completed", started_at=1000.0, ended_at=1600.0)
    page = _render(root, tmp_path, "i.html")
    assert "Running now" not in page


def test_s137rc_two_running_seasons_two_cells(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    (root / "seasons" / "s2.yaml").write_text(
        "id: s2\ngoal: fixture goal for s2\n", encoding="utf-8"
    )
    _write_state(root, "s1", status="running", started_at=1000.0)
    _write_state(root, "s2", status="running", started_at=2000.0)
    page = _render(root, tmp_path, "i.html")
    card = _running_card(page)
    assert card.count("<li>") == 2
    assert "<strong>s1</strong>" in card
    assert "<strong>s2</strong>" in card
    assert "1970-01-01T00:16:40+00:00" in card
    assert "1970-01-01T00:33:20+00:00" in card
