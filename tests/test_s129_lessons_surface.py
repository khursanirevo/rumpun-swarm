"""s129 w2 pins: the lessons file becomes a first-class read.

Spec source: the s129 w2 brief. The sibling seeded .rumpun/lessons.md
and the s124 disclosure said read it before composing briefs. The
index should say it exists. Honest shape: present -> the index renders
the entry count (bullet lines are entries), absent -> the page is
byte-identical, silence not an empty promise. The file is a persisted
read (the M1 contract), no clock. Fixture discipline: tmp campaigns,
the lessons file is synthesized per pin, no real writes.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 pre-implementation, /tmp/s129-w2-pins-red.txt.
- GREEN captured 2026-09-20 post-implementation, /tmp/s129-w2-pins-green.txt.
- The determinism guard is green on both sides by design.
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


def test_s129ls_absent_file_index_bytes_unchanged(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    a = _render(root, tmp_path, "ia.html")
    body = _render(root, tmp_path, "ib.html")
    assert a == body
    assert "Campaign lessons" not in a


def test_s129ls_present_file_renders_entry_count(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    (root / "lessons.md").write_text(
        "- lesson one\n"
        "\n"
        "not an entry\n"
        "- lesson two\n"
        "- lesson three\n",
        encoding="utf-8",
    )
    html = _render(root, tmp_path, "i.html")
    assert "<h2>Campaign lessons</h2>" in html
    assert "<strong>3</strong> lessons on file" in html
    again = _render(root, tmp_path, "i2.html")
    assert html == again


def test_s129ls_count_tracks_file_growth(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    lessons = root / "lessons.md"
    lessons.write_text("- one\n- two\n", encoding="utf-8")
    first = _render(root, tmp_path, "i1.html")
    assert "<strong>2</strong> lessons on file" in first
    lessons.write_text("- one\n- two\n- three\n- four\n", encoding="utf-8")
    second = _render(root, tmp_path, "i2.html")
    assert "<strong>4</strong> lessons on file" in second


def test_s129ls_present_empty_file_still_counts(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    (root / "lessons.md").write_text("", encoding="utf-8")
    html = _render(root, tmp_path, "i.html")
    assert "<strong>0</strong> lessons on file" in html
