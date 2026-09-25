"""s113 w2 pins — the machine report renders the marks.

Spec source: the s113 w2 brief. The epic view carries the basis, the panel
mark, and the dissent mark; the deterministic report still shows bare exits.
Ground truth measured 2026-09-20: five live dissent seasons (s69, s74, s77,
s79, s83 via `rumpun epics`) and zero incomplete keys in live
runs/*/_season/state.json and results.jsonl (the s112 gate has not caught a
notes-less exit yet).

The marks:
- an agent snap carrying the additive incomplete key (the s112 notes gate,
  engine._agent_snap) renders the mark beside its measured row on the
  season page's agent table; state and exit_code stay the measured values;
  the header keeps its five columns so unmarked pages keep their bytes.
- a season whose member data yields a dissent renders the dissent mark in
  its campaign-strip cell, on season pages and the index alike. The mark
  comes from the epics.py resolution (season_verdict, the
  highest-generation panel-<sid>-verdict record), imported, not re-derived.

Determinism (the M1 contract): identical persisted bytes render identical
pages; the marks read only persisted files (state.json, verdicts.jsonl, the
ledger), no clock reads, sorted orders.

Fixture discipline: everything synthesized in tmp_path; ledger records come
only from the real akar.append_record path (the s112 dissent-pin pattern);
nothing is copied from .rumpun/runs/ (the check-s110 class). Strip
membership needs seasons/s<N>.yaml (report._season_ids reads the stems), so
the builder writes yamls alongside run state.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 pre-implementation; /tmp/s113-w2-pins-red.txt.
- GREEN captured 2026-09-20 post-implementation; /tmp/s113-w2-pins-green.txt.
- The bare-exit and determinism pins are guards: green on both sides by
  design, so a regression cannot mark a healthy writer, move the table
  shape, or break the M1 byte contract.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from rumpun import akar


def _s113marks_report():
    """The render under test; a missing module fails naming the spec reason."""
    try:
        from rumpun import report
    except ImportError as exc:
        pytest.fail(f"src/rumpun/report.py missing/unimportable: {exc}")
    return report


def _s113marks_snap(name: str, *, incomplete: str | None = None) -> dict[str, Any]:
    """The persisted snap shape (engine._agent_snap), rc-0 exit; the additive
    incomplete key rides beside the measured state and exit_code."""
    snap: dict[str, Any] = {
        "name": name,
        "route": "fixture",
        "state": "exited",
        "exit_code": 0,
        "started_at": 1000.0,
        "seconds": 60.0,
    }
    if incomplete:
        snap["incomplete"] = incomplete
    return snap


def _s113marks_season(
    root: Path,
    sid: str,
    agents: dict[str, dict[str, Any]] | None = None,
    verdict: str | None = None,
) -> None:
    """One season: yaml (strip membership), persisted run state, optional
    harvest verdict row."""
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
        "agents": agents or {},
    }
    (season / "state.json").write_text(json.dumps(state), encoding="utf-8")
    if verdict:
        (root / "runs" / sid / "verdicts.jsonl").write_text(
            json.dumps({"season": sid, "verdict": verdict}) + "\n",
            encoding="utf-8",
        )


def _s113marks_panel(root: Path, rid: str, status: str) -> None:
    """A sealed panel verdict record via the real append path."""
    akar.append_record(
        root,
        rid,
        f"panel verdict ({status})",
        f"status: {status}\nroute: fixture (bounded 300s)\nreply:\nverdict: {status}",
    )


def _s113marks_root(tmp_path: Path) -> Path:
    root = tmp_path / "s113proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "runs").mkdir()
    (root / "ledger").mkdir()
    return root


def _s113marks_cells(page: str) -> dict[str, str]:
    """Strip cells keyed by season id."""
    cells: dict[str, str] = {}
    for m in re.finditer(r'<div class="cell">.*?</div>', page, flags=re.S):
        cell = m.group(0)
        sid_m = re.search(r'<span class="sid">([^<]+)</span>', cell)
        if sid_m:
            cells[sid_m.group(1)] = cell
    return cells


def _s113marks_rows(page: str) -> dict[str, str]:
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


def test_s113marks_agent_incomplete_cell(tmp_path: Path) -> None:
    """The mark: the marked agent's row names the gap; state and exit_code
    stay the measured values; the clean agent's row and the five-column
    header stay exactly as before."""
    report = _s113marks_report()
    root = _s113marks_root(tmp_path)
    _s113marks_season(
        root,
        "s1",
        agents={
            "w1": _s113marks_snap("w1", incomplete="notes.md missing"),
            "w2": _s113marks_snap("w2"),
        },
        verdict="WIN",
    )
    out = tmp_path / "s1.html"
    report.render_report(root, "s1", out)
    page = out.read_text(encoding="utf-8")
    rows = _s113marks_rows(page)
    assert "incomplete: notes.md missing" in rows["w1"]
    assert "incomplete" not in rows["w2"]
    assert "<td>exited</td>" in rows["w1"]
    assert "<td>0</td>" in rows["w1"]
    thead = page.split("<thead>")[1].split("</thead>")[0]
    assert thead.count("<th>") == 5, "agent-table header keeps its five columns"
    assert page.count("incomplete") == 1, "exactly one mark on the page"


def test_s113marks_bare_exit_stays_unmarked(tmp_path: Path) -> None:
    """Guard: a season whose snaps carry no incomplete key renders no mark
    (the word absent from the page entirely)."""
    report = _s113marks_report()
    root = _s113marks_root(tmp_path)
    _s113marks_season(root, "s1", agents={"w1": _s113marks_snap("w1")}, verdict="LOSS")
    out = tmp_path / "s1.html"
    report.render_report(root, "s1", out)
    assert "incomplete" not in out.read_text(encoding="utf-8")


def test_s113marks_render_determinism_with_marks(tmp_path: Path) -> None:
    """Guard (the M1 contract): two renders of the same persisted bytes are
    byte-identical, both marks included."""
    report = _s113marks_report()
    root = _s113marks_root(tmp_path)
    _s113marks_season(
        root,
        "s1",
        agents={"w1": _s113marks_snap("w1", incomplete="notes.md missing")},
        verdict="WIN",
    )
    _s113marks_season(root, "s3", verdict="WIN")
    _s113marks_panel(root, "panel-s3-verdict", "LOSS")
    first = report.render_report(root, "s1", tmp_path / "a.html")
    second = report.render_report(root, "s1", tmp_path / "b.html")
    assert first.read_bytes() == second.read_bytes()


def test_s113marks_strip_names_dissent(tmp_path: Path) -> None:
    """The dissent mark renders in the campaign-strip cell of a season whose
    member data yields a dissent (harvest verdict plus latest panel verdict,
    divergent), on the season page and the index alike. Seasons missing
    either side, or with agreeing verdicts, stay bare."""
    report = _s113marks_report()
    root = _s113marks_root(tmp_path)
    _s113marks_season(root, "s3", verdict="WIN")
    _s113marks_panel(root, "panel-s3-verdict", "LOSS")
    _s113marks_season(root, "s4", verdict="WIN")  # no panel record
    _s113marks_season(root, "s5", verdict="WIN")  # agreeing panel verdict
    _s113marks_panel(root, "panel-s5-verdict", "WIN")
    _s113marks_season(root, "s6")  # no harvest verdict row
    _s113marks_panel(root, "panel-s6-verdict", "LOSS")
    # yaml only: strip membership without run state (the render must
    # survive it, and the cell stays bare)
    (root / "seasons" / "s9.yaml").write_text(
        "id: s9\ngoal: fixture goal for s9\n", encoding="utf-8"
    )
    page = report.render_report(root, "s3", tmp_path / "s3.html").read_text(
        encoding="utf-8"
    )
    cells = _s113marks_cells(page)
    assert ">dissent:LOSS</span>" in cells["s3"]
    assert all("dissent" not in cells[sid] for sid in ("s4", "s5", "s6"))
    assert "no state" in cells["s9"], "the render survives a yaml-only season"
    assert "dissent" not in cells["s9"]
    index = report.render_index(root, tmp_path / "index.html").read_text(
        encoding="utf-8"
    )
    icells = _s113marks_cells(index)
    assert ">dissent:LOSS</span>" in icells["s3"]
    assert all("dissent" not in icells[sid] for sid in ("s4", "s5", "s6"))


def test_s113marks_dissent_generation_convention(tmp_path: Path) -> None:
    """The s108 rerun convention rides along unmodified: the highest verdict
    generation wins (a newer agreeing verdict hides an older dissent), and a
    newer generation holding only an error never hides the sealed verdict
    behind it."""
    report = _s113marks_report()
    root = _s113marks_root(tmp_path)
    _s113marks_season(root, "s7", verdict="WIN")
    _s113marks_panel(root, "panel-s7-verdict", "LOSS")  # gen 1: divergent
    _s113marks_panel(root, "panel-s7-2-verdict", "WIN")  # gen 2: agreeing
    _s113marks_season(root, "s8", verdict="WIN")
    _s113marks_panel(root, "panel-s8-verdict", "LOSS")  # gen 1: divergent
    akar.append_record(
        root, "panel-s8-2-error", "panel error s8",
        "status: error\nroute: fixture (bounded 300s)\nreply:\nerror: fixture",
    )
    page = report.render_report(root, "s7", tmp_path / "s7.html").read_text(
        encoding="utf-8"
    )
    cells = _s113marks_cells(page)
    assert "dissent" not in cells["s7"], "gen-2 WIN hides the gen-1 LOSS"
    assert ">dissent:LOSS</span>" in cells["s8"], "an error never hides a verdict"
