"""s133 w2 pins: the dashboard carries the audit's candidates.

Spec source: the s133 w2 brief. The fronts card carries the standing
decisions; the audit's current candidates live in the ledger only. The
index renders the newest audit-* record's candidate lines in one card,
verbatim (escaped like every quoted truth). Newest = max by (date, N)
over the YYYY-MM-DD_audit-N.md filenames: audit-48 outranks audit-47.
The honest shape: record present with candidate lines -> the card
renders them; absent, unreadable, or findings-only -> byte-identical
page (the M1 contract, the s129/s131/s132 precedent). Fixture
discipline: tmp campaigns, the audit record is synthesized per pin, no
real writes.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 pre-implementation, /tmp/s133-w2-pins-red.txt.
- GREEN captured 2026-09-20 post-implementation, /tmp/s133-w2-pins-green.txt.
- The absence pins are green on both sides by design; the positive
  controls are the present-record pins in the same run. Two draft
  corrections landed before the GREEN capture: the findings-only pin
  compares same-state renders (an audit record is itself a discovery
  by design, so any record shifts the page), and the unreadable pin
  asserts the reader contract (report._audit_candidates returns None)
  instead of page-wide silence: bad utf-8 in any ledger file crashes
  the strip tally through akar._declared (akar.py:51), a reader
  outside this lane's edit bounds. The page-wide decode gap is named
  in notes.md for the audit.
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


def _candidates_card(page: str) -> str:
    """The Audit candidates card slice; fails by name when the card is absent."""
    start = page.find("<h2>Audit candidates")
    assert start != -1, "the Audit candidates card is missing"
    end = page.find("</section>", start)
    return page[start:end]


def _audit_record(n: int, candidates: list[str]) -> str:
    lines = [
        f"# akar record: audit-{n}",
        f"id: audit-{n}",
        "date: 2026-09-20",
        "title: reflection audit",
    ]
    lines.extend(f"candidate: {text}" for text in candidates)
    return "\n".join(lines) + "\n"


def test_s133ac_absent_record_byte_identical(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    a = _render(root, tmp_path, "ia.html")
    body = _render(root, tmp_path, "ib.html")
    assert a == body
    assert "Audit candidates" not in a


def test_s133ac_present_record_renders_candidates(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    ledger = root / "ledger"
    ledger.mkdir()
    (ledger / "2026-09-20_audit-48.md").write_text(
        _audit_record(
            48,
            [
                "s30 and s32 count post-stop integration as WIN (usefulness-decade-1)",
                "the cost accounting stays the operator's front (usefulness-decade-1)",
                "keep the <em>verbatim</em> text escaped (usefulness-decade-1)",
            ],
        ),
        encoding="utf-8",
    )
    page = _render(root, tmp_path, "i.html")
    card = _candidates_card(page)
    assert card.count("<li>") == 3
    assert "s30 and s32 count post-stop integration as WIN" in card
    assert "the operator&#x27;s front" in card
    assert "&lt;em&gt;verbatim&lt;/em&gt;" in card
    assert "<em>verbatim</em>" not in card
    again = _render(root, tmp_path, "i2.html")
    assert page == again


def test_s133ac_newest_record_wins(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    ledger = root / "ledger"
    ledger.mkdir()
    (ledger / "2026-09-18_audit-47.md").write_text(
        _audit_record(47, ["stale candidate from audit-47 (usefulness-decade-1)"]),
        encoding="utf-8",
    )
    (ledger / "2026-09-20_audit-48.md").write_text(
        _audit_record(48, ["fresh candidate from audit-48 (usefulness-decade-2)"]),
        encoding="utf-8",
    )
    card = _candidates_card(_render(root, tmp_path, "i.html"))
    assert "fresh candidate from audit-48" in card
    assert "stale candidate from audit-47" not in card


def test_s133ac_findings_only_silent(tmp_path: Path) -> None:
    root = _proj(tmp_path)
    ledger = root / "ledger"
    ledger.mkdir()
    (ledger / "2026-09-20_audit-48.md").write_text(
        _audit_record(48, []), encoding="utf-8"
    )
    page = _render(root, tmp_path, "ia.html")
    assert "Audit candidates" not in page
    again = _render(root, tmp_path, "i2.html")
    assert page == again


def test_s133ac_unreadable_record_reader_silent(tmp_path: Path) -> None:
    """The card's reader returns None on unreadable newest-record bytes.

    Page-wide silence is unreachable in-bounds: bad utf-8 in any ledger
    file crashes the strip tally through akar._declared first (see the
    color history). The card reads through its own guarded read.
    """
    root = _proj(tmp_path)
    ledger = root / "ledger"
    ledger.mkdir()
    (ledger / "2026-09-20_audit-48.md").write_bytes(b"\xff\xfe not utf-8 \xff")
    assert report._audit_candidates(root) is None
