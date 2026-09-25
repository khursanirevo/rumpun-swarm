"""s145 w2 record: the fronts file refreshed current against RESUME.

Spec source: the s145 w2 brief. .rumpun/operator-fronts.yaml drifts as
closes land, so the refresh lane re-reads .rumpun/RESUME.md's open
items line and re-lands the entries verbatim. This file is the lane's
record: the refresh date and the measured entries are embedded below,
and the pins read the standing file read-only - no writes, no tmp_path
synthesis, no reads of live run state. The refresh ran on 2026-09-21
against the s144-close RESUME (the s145 w2 lane) and measured
zero-delta; it re-ran at s146 w2 against the s145-close RESUME the
same day and measured zero-delta again - the standing entries match
the open items line verbatim, the parsed content is unchanged. The
s138 format pins stand unchanged; this record pins content, not format.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

FRONTS = Path(__file__).resolve().parents[1] / ".rumpun" / "operator-fronts.yaml"

REFRESH_DATE = "2026-09-21"

ENTRIES: list[str] = [
    "the forge merge decision table (operator)",
    "issue #18 (the cost accounting, the operator's front, stay-open; "
    "the spend aggregation landed as the measurable half)",
    "the external-outcome residual stands with the operator's (a) "
    "keeping internal seasons running",
    "the kancil upgrade is the operator's (the strict-xfail alarm names it)",
]


def test_s145fr2_record_shape() -> None:
    """The record: a dated refresh, four owner-complete non-empty entries."""
    assert date.fromisoformat(REFRESH_DATE).isoformat() == REFRESH_DATE
    assert len(ENTRIES) == 4
    assert all(entry.strip() and "operator" in entry.lower() for entry in ENTRIES)


def test_s145fr2_file_carries_recorded_entries_verbatim() -> None:
    """The standing file reads back exactly the recorded measured entries."""
    data = yaml.safe_load(FRONTS.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert data == ENTRIES
