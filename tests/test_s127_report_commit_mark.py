"""s127 w2 pins — the report renders the attested commit.

Spec source: the s127 w2 brief. Results rows have named each lane's commit
since s123; the report page (what the operator reads) does not show it.
Ground truth measured 2026-09-20: engine._agent_snap writes the additive
commit key when HEAD moved past head_at_spawn (terminal states only) and
_write_results passes it into results.jsonl (attested in production at
s124 and s125); report._agent_rows renders the persisted state.json snaps
and has no commit rendering (the M1 determinism contract; the s113 marks
and the s124 stall marks are the precedents).

The mark:
- an agent snap carrying the additive commit key renders the sha beside
  its measured row on the season page's agent table; state and exit_code
  stay the measured values; the header keeps its five columns so
  unmarked pages keep their bytes.
- rows without the key stay bare: the word "commit" is absent from the
  page (guard, green on both sides by design).
- identical persisted bytes render byte-identical pages, mark included
  (the M1 contract, the s113 determinism precedent).

Fixture discipline: everything synthesized in tmp_path; snaps follow the
engine snap shape; nothing is copied from .rumpun/runs/ (the check-s110
class). Strip membership needs seasons/s<N>.yaml (report._season_ids
reads the stems), so the builder writes yamls alongside run state.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 pre-implementation; /tmp/s127-w2-pins-red.txt.
- GREEN captured 2026-09-20 post-implementation; /tmp/s127-w2-pins-green.txt.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest


def _s127cm_report():
    """The render under test; a missing module fails naming the spec reason."""
    try:
        from rumpun import report
    except ImportError as exc:
        pytest.fail(f"src/rumpun/report.py missing/unimportable: {exc}")
    return report


def _s127cm_snap(name: str, *, commit: str | None = None) -> dict[str, Any]:
    """The persisted snap shape (engine._agent_snap), rc-0 exit; the
    additive commit key rides beside the measured state and exit_code."""
    snap: dict[str, Any] = {
        "name": name,
        "route": "fixture",
        "state": "exited",
        "exit_code": 0,
        "started_at": 1000.0,
        "seconds": 60.0,
    }
    if commit:
        snap["commit"] = commit
    return snap


def _s127cm_season(root: Path, sid: str, agents: dict[str, dict[str, Any]]) -> None:
    """One season: yaml (strip membership) plus the persisted run state."""
    (root / "seasons" / f"{sid}.yaml").write_text(
        f"id: {sid}\ngoal: fixture goal for {sid}\n", encoding="utf-8"
    )
    season = root / "runs" / sid / "_season"
    season.mkdir(parents=True, exist_ok=True)
    state = {
        "id": sid,
        "status": "completed",
        "started_at": 1000.0,
        "ended_at": 1600.0,
        "agents": agents,
    }
    (season / "state.json").write_text(json.dumps(state), encoding="utf-8")


def _s127cm_root(tmp_path: Path) -> Path:
    root = tmp_path / "s127proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "runs").mkdir()
    (root / "ledger").mkdir()
    return root


def _s127cm_rows(page: str) -> dict[str, str]:
    """Agent-table body rows keyed by the agent name cell. The page's first
    tbody is the agent table; the later workspaces table is excluded."""
    rows: dict[str, str] = {}
    tbody = page.split("<tbody>")[1].split("</tbody>")[0]
    for m in re.finditer(r"<tr>(.*?)</tr>", tbody, flags=re.S):
        row = m.group(0)
        name_m = re.search(r"<td>([^<]*)</td>", row)
        if name_m:
            rows[name_m.group(1)] = row
    return rows


def test_s127cm_agent_commit_cell(tmp_path: Path) -> None:
    """The mark: the committed agent's row names the sha; state and
    exit_code stay the measured values; the clean agent's row and the
    five-column header stay exactly as before."""
    report = _s127cm_report()
    root = _s127cm_root(tmp_path)
    _s127cm_season(
        root,
        "s1",
        agents={
            "w1": _s127cm_snap("w1", commit="a1b2c3d4e5f6a7b8"),
            "w2": _s127cm_snap("w2"),
        },
    )
    out = tmp_path / "s1.html"
    report.render_report(root, "s1", out)
    page = out.read_text(encoding="utf-8")
    rows = _s127cm_rows(page)
    assert "commit: a1b2c3d4e5f6a7b8" in rows["w1"]
    assert "commit" not in rows["w2"]
    assert "<td>exited</td>" in rows["w1"]
    assert "<td>0</td>" in rows["w1"]
    thead = page.split("<thead>")[1].split("</thead>")[0]
    assert thead.count("<th>") == 5, "agent-table header keeps its five columns"


def test_s127cm_rows_without_commit_stay_bare(tmp_path: Path) -> None:
    """Guard: a season whose snaps carry no commit key renders no mark (the
    word absent from the page entirely; the M1 byte contract holds)."""
    report = _s127cm_report()
    root = _s127cm_root(tmp_path)
    _s127cm_season(root, "s1", agents={"w1": _s127cm_snap("w1")})
    out = tmp_path / "s1.html"
    report.render_report(root, "s1", out)
    assert "commit" not in out.read_text(encoding="utf-8")


def test_s127cm_render_determinism_with_commit(tmp_path: Path) -> None:
    """Guard (the M1 contract): two renders of the same persisted bytes are
    byte-identical, the commit mark included."""
    report = _s127cm_report()
    root = _s127cm_root(tmp_path)
    _s127cm_season(
        root, "s1", agents={"w1": _s127cm_snap("w1", commit="a1b2c3d4e5f6a7b8")}
    )
    first = report.render_report(root, "s1", tmp_path / "a.html")
    second = report.render_report(root, "s1", tmp_path / "b.html")
    assert first.read_bytes() == second.read_bytes()
