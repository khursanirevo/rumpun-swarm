"""s132 w2 pins: the report index carries the writer-seconds spend.

Spec source: the s132 w2 brief (issue #18's measurable half). The
committed DESIGN.md season rows carry writer-seconds ("both writers
exited clean at 1743s"); the campaign never totals them. The index
renders one spend cell with the sum. Absent record, no figures, or an
unreadable record -> byte-identical page (the M1 contract, the
s129/s131 precedent). The wall-clock verdict times ("stopped_stall at
900s") carry no writer subject and stay uncounted (the negative
control). Fixture discipline: tmp campaigns, DESIGN.md synthesized per
pin, no real writes.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 pre-implementation, /tmp/s132-w2-pins-red.txt.
- GREEN captured 2026-09-20 post-implementation, /tmp/s132-w2-pins-green.txt.
- The absence pins are green on both sides by design; the positive
  controls are the two present-rows pins in the same run.
"""

from __future__ import annotations

import json
from pathlib import Path

from rumpun import report

_HEADER = (
    "# DESIGN rows\n\n"
    "| season | verdict | ships (one line) |\n"
    "|---|---|---|\n"
)


def _proj(tmp_path: Path) -> Path:
    """Tmp campaign: the .rumpun skeleton plus one stopped season."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "runs" / "s1" / "_season").mkdir(parents=True)
    (root / "seasons" / "s1.yaml").write_text(
        "id: s1\ngoal: fixture goal for s1\n", encoding="utf-8"
    )
    state = {
        "id": "s1",
        "status": "stopped",
        "started_at": 1000.0,
        "ended_at": 1600.0,
        "agents": {},
    }
    (root / "runs" / "s1" / "_season" / "state.json").write_text(
        json.dumps(state), encoding="utf-8"
    )
    return root


def _render(root: Path, tmp_path: Path, name: str) -> str:
    return report.render_index(root, tmp_path / name).read_text(encoding="utf-8")


def _spend_card(html: str) -> str:
    """The Writer spend card slice; fails by name when the card is absent."""
    start = html.find("<h2>Writer spend")
    assert start != -1, "the Writer spend card is missing"
    end = html.find("</section>", start)
    return html[start:end]


def test_s132sp_absent_design_byte_identical(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    a = _render(root, tmp_path, "ia.html")
    body = _render(root, tmp_path, "ib.html")
    assert a == body
    assert "Writer spend" not in a


def test_s132sp_rows_without_writer_seconds_byte_identical(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    (root.parent / "DESIGN.md").write_text(
        _HEADER +
        "| s15 | LOSS (stopped_stall at 900s; band unmet) | the replay ran | \n"
        "| s130 | WIN (band clauses met) | the exhaustion rehearsal | \n",
        encoding="utf-8",
    )
    a = _render(root, tmp_path, "ia.html")
    body = _render(root, tmp_path, "ib.html")
    assert a == body
    assert "Writer spend" not in a


def test_s132sp_present_rows_render_the_total(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    (root.parent / "DESIGN.md").write_text(
        _HEADER +
        "| s67 | WIN (w1 stall-terminated at 2351s, w2 exited clean) | the forge flow | \n"
        "| s68 | WIN (both writers exited clean at 1743s) | the kancil forge | \n"
        "| s130 | WIN (band clauses met) | the rehearsal | \n",
        encoding="utf-8",
    )
    html = _render(root, tmp_path, "i.html")
    card = _spend_card(html)
    assert "<strong>4094</strong>" in card
    assert "writer-seconds" in card
    again = _render(root, tmp_path, "i2.html")
    assert html == again


def test_s132sp_mixed_rows_count_writer_figures_only(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    (root.parent / "DESIGN.md").write_text(
        _HEADER +
        "| s68 | WIN (both writers exited clean at 1743s) | stopped_budget at 1500s, no writer | \n"
        "| s15 | LOSS (stopped_stall at 900s) | the replay | \n",
        encoding="utf-8",
    )
    html = _render(root, tmp_path, "i.html")
    card = _spend_card(html)
    assert "<strong>1743</strong>" in card
    assert "1500" not in card
    assert "900" not in card
