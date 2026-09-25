"""s131 w1 pins: the standing decisions surface where the operator reads.

Spec source: the s131 w1 brief. The operator-gated items live in the
RESUME open items and the ledger, but the operator reads the report
index. .rumpun/operator-fronts.yaml carries the standing decisions,
one entry per operator front (the forge table, issue #18, the kancil
upgrade, the external workload). Honest shape: the file present ->
the index renders one cell per entry, verbatim; absent or empty ->
byte-identical silence (the s129 M1 contract). A persisted read only,
unreadable stays silent. Fixture discipline: tmp campaigns, the
fronts file is synthesized per pin, no real writes.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 pre-implementation, /tmp/s131-w1-pins-red.txt.
- GREEN captured 2026-09-20 post-implementation, /tmp/s131-w1-pins-green.txt.
- The absence pins are green on both sides by design; the positive
  control is the present-file pin in the same run.
"""

from __future__ import annotations

import json
from pathlib import Path

from rumpun import report


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


def _fronts_card(html: str) -> str:
    """The Standing decisions card slice, asserted present."""
    start = html.find("<h2>Standing decisions")
    assert start != -1, "the Standing decisions card is missing"
    end = html.find("</section>", start)
    return html[start:end]


def test_s131of_absent_file_index_bytes_unchanged(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    a = _render(root, tmp_path, "ia.html")
    body = _render(root, tmp_path, "ib.html")
    assert a == body
    assert "Standing decisions" not in a


def test_s131of_present_file_renders_one_cell_per_entry(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    (root / "operator-fronts.yaml").write_text(
        '- "the forge merge decision table (operator)"\n'
        '- "issue #18 (the cost accounting, the operator\'s front, stay-open)"\n'
        '- "the kancil upgrade is the operator\'s"\n',
        encoding="utf-8",
    )
    html = _render(root, tmp_path, "i.html")
    card = _fronts_card(html)
    assert card.count("<li>") == 3
    assert "the forge merge decision table (operator)" in card
    assert (
        "issue #18 (the cost accounting, the operator&#x27;s front, stay-open)" in card
    )
    assert "the kancil upgrade is the operator&#x27;s" in card
    again = _render(root, tmp_path, "i2.html")
    assert html == again


def test_s131of_empty_file_byte_identical(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    (root / "operator-fronts.yaml").write_text("", encoding="utf-8")
    with_file = _render(root, tmp_path, "ie.html")
    (root / "operator-fronts.yaml").unlink()
    without_file = _render(root, tmp_path, "in.html")
    assert with_file == without_file
    assert "Standing decisions" not in with_file


def test_s131of_entries_render_verbatim_and_escaped(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    (root / "operator-fronts.yaml").write_text(
        '- "keep the <em>operator</em> front open"\n',
        encoding="utf-8",
    )
    html = _render(root, tmp_path, "i.html")
    card = _fronts_card(html)
    assert "keep the &lt;em&gt;operator&lt;/em&gt; front open" in card
    assert "<em>operator</em>" not in card


def test_s131of_unreadable_file_stays_silent(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    (root / "operator-fronts.yaml").write_text("::: not yaml [\n", encoding="utf-8")
    broken = _render(root, tmp_path, "ibroken.html")
    (root / "operator-fronts.yaml").unlink()
    without_file = _render(root, tmp_path, "in2.html")
    assert broken == without_file


def test_s131of_non_list_body_stays_silent(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    (root / "operator-fronts.yaml").write_text(
        "fronts: not a list\n", encoding="utf-8"
    )
    html = _render(root, tmp_path, "i.html")
    assert "Standing decisions" not in html
    again = _render(root, tmp_path, "i2.html")
    assert html == again
