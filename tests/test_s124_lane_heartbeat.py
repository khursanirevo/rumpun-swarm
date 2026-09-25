"""s124 w1 pins — the lane heartbeat makes silence an event.

Spec source: the s124 w1 brief. A running lane past its stall window
with no progress is the signal; the loop tick publishes one
lane-stalled event per stalled lane (season, lane, last-progress) and
sweeps the event when the lane moves again or the season stops
(idempotent per lane-stall: one stall is one file, however many ticks
it survives). The report renders the mark beside the lane's row on the
season page and in the campaign-strip cell on season pages and the
index. Ground truth measured 2026-09-20: the tick rides loop.run
(the close-prep and the draft hand-off already ride it); the stall
decision is the engine snap's "stalled" state (the history-less reader
the status verb uses); the last-progress anchor is the workspace
state.json stamp set the snap reads (started_at floor, then the
durable stamps). Fixture discipline: tmp campaigns only; no real
event writes; the report renders from persisted files, no clock.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 pre-implementation; /tmp/s124-w1-pins-red.txt.
- GREEN captured 2026-09-20 post-implementation; /tmp/s124-w1-pins-green.txt.
- The quiet-lane guard and the determinism pin are guards: green on
  both sides by design.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rumpun import engine, loop, report

STALL_S = 5.0


def _proj(tmp_path: Path) -> Path:
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    (root / "runs").mkdir()
    for sid in ("s1", "s2"):
        (root / "seasons" / f"{sid}.yaml").write_text(
            f"id: {sid}\ngoal: fixture goal for {sid}\n", encoding="utf-8"
        )
    return root


def _lane(
    root: Path, sid: str, lane: str, *, stalled: bool = True
) -> float:
    """One live lane workspace; returns its last-progress anchor.

    Live via this process's pid and proc_start (the boot-recovery
    convention). The stall anchor rides the s24 scan-stamp route:
    log_size plus last_progress in the meta, so mtime plays no part.
    """
    ws = root / "runs" / sid / lane
    ws.mkdir(parents=True, exist_ok=True)
    now = time.time()
    meta: dict[str, Any] = {
        "name": lane,
        "route": "fixture",
        "pid": os.getpid(),
        "proc_start": engine._proc_start_ticks(os.getpid()),
        "started_at": now - 200.0,
        "log_size": 12,
    }
    anchor = now - 100.0 if stalled else now
    meta["last_progress"] = anchor
    (ws / "state.json").write_text(json.dumps(meta), encoding="utf-8")
    (ws / "agent.log").write_text("fixture log\n", encoding="utf-8")
    return anchor


def _running_season(
    root: Path, sid: str, agents: dict[str, dict[str, Any]] | None = None
) -> None:
    """Persisted running state; read_status recomputes live snaps."""
    season = root / "runs" / sid / "_season"
    season.mkdir(parents=True, exist_ok=True)
    state = {
        "id": sid,
        "status": "running",
        "started_at": time.time() - 300.0,
        "stall_s": STALL_S,
        "agents": agents or {},
    }
    (season / "state.json").write_text(json.dumps(state), encoding="utf-8")


def _snap(name: str) -> dict[str, Any]:
    """The persisted snap shape (engine._agent_snap), still running."""
    return {
        "name": name,
        "route": "fixture",
        "state": "running",
        "exit_code": None,
        "started_at": 1000.0,
        "seconds": 60.0,
    }


def _stopped(root: Path, sid: str, status: str) -> None:
    season = root / "runs" / sid / "_season"
    state = json.loads((season / "state.json").read_text(encoding="utf-8"))
    state["status"] = status
    (season / "state.json").write_text(json.dumps(state), encoding="utf-8")


def _event(root: Path, sid: str, lane: str) -> Path:
    return root / "events" / f"lane-stalled-{sid}-{lane}.json"


def _iso(anchor: float) -> str:
    return datetime.fromtimestamp(anchor, tz=timezone.utc).isoformat(
        timespec="seconds"
    )


def test_s124hb_emits_one_event_per_stalled_lane(tmp_path: Path) -> None:
    """The mark's source: a running season's stalled lane gets one named
    event carrying season, lane, and the last-progress anchor."""
    root = _proj(tmp_path)
    anchor = _lane(root, "s1", "w1", stalled=True)
    _running_season(root, "s1")
    assert loop.run(root, once=True) == 0
    path = _event(root, "s1", "w1")
    assert path.is_file(), "the tick emits the named event"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["kind"] == "lane-stalled"
    assert payload["season"] == "s1"
    assert payload["lane"] == "w1"
    assert payload["last_progress"] == anchor


def test_s124hb_idempotent_per_lane_stall(tmp_path: Path) -> None:
    """One stall, one file: repeated ticks during the same stall keep the
    same single event, and a later stall of the same lane re-anchors the
    same file to the new last-progress stamp."""
    root = _proj(tmp_path)
    _lane(root, "s1", "w1", stalled=True)
    _running_season(root, "s1")
    assert loop.run(root, once=True) == 0
    assert loop.run(root, once=True) == 0
    files = sorted((root / "events").glob("lane-stalled-*.json"))
    assert [p.name for p in files] == ["lane-stalled-s1-w1.json"]
    ws = root / "runs" / "s1" / "w1" / "state.json"
    meta = json.loads(ws.read_text(encoding="utf-8"))
    anchor2 = time.time() - 100.0
    meta["last_progress"] = anchor2
    ws.write_text(json.dumps(meta), encoding="utf-8")
    assert loop.run(root, once=True) == 0
    files = sorted((root / "events").glob("lane-stalled-*.json"))
    assert [p.name for p in files] == ["lane-stalled-s1-w1.json"]
    payload = json.loads(_event(root, "s1", "w1").read_text(encoding="utf-8"))
    assert payload["last_progress"] == anchor2


def test_s124hb_resume_sweeps_the_event(tmp_path: Path) -> None:
    """The bus holds exactly the live stalls: when the lane moves again,
    the next tick removes its event."""
    root = _proj(tmp_path)
    _lane(root, "s1", "w1", stalled=True)
    _running_season(root, "s1")
    assert loop.run(root, once=True) == 0
    assert _event(root, "s1", "w1").is_file()
    ws = root / "runs" / "s1" / "w1" / "state.json"
    meta = json.loads(ws.read_text(encoding="utf-8"))
    meta["last_progress"] = time.time()
    ws.write_text(json.dumps(meta), encoding="utf-8")
    assert loop.run(root, once=True) == 0
    assert not _event(root, "s1", "w1").exists(), "resumed lane swept"


def test_s124hb_stopped_season_sweeps_the_event(tmp_path: Path) -> None:
    """A season that stopped while its lane's event sat on the bus loses
    the event at the next tick: no mark outlives its season."""
    root = _proj(tmp_path)
    _lane(root, "s1", "w1", stalled=True)
    _running_season(root, "s1")
    assert loop.run(root, once=True) == 0
    assert _event(root, "s1", "w1").is_file()
    _stopped(root, "s1", "stopped_stall")
    assert loop.run(root, once=True) == 0
    assert not _event(root, "s1", "w1").exists(), "stopped season swept"


def test_s124hb_quiet_lanes_stay_quiet(tmp_path: Path) -> None:
    """Guard: a fresh lane and a yaml-only season publish nothing and
    break no tick."""
    root = _proj(tmp_path)
    _lane(root, "s1", "w1", stalled=False)
    _running_season(root, "s1")
    assert loop.run(root, once=True) == 0
    assert list((root / "events").glob("lane-stalled-*.json")) == []


def test_s124hb_report_row_mark(tmp_path: Path) -> None:
    """The report renders the mark: the stalled lane's row names the gap
    beside its measured values; the clean row and the five-column header
    keep their bytes."""
    root = _proj(tmp_path)
    anchor = _lane(root, "s1", "w1", stalled=True)
    _running_season(
        root, "s1", agents={"w1": _snap("w1"), "w2": _snap("w2")}
    )
    assert loop.run(root, once=True) == 0
    out = tmp_path / "s1.html"
    report.render_report(root, "s1", out)
    page = out.read_text(encoding="utf-8")
    rows: dict[str, str] = {}
    tbody = page.split("<tbody>")[1].split("</tbody>")[0]
    for m in re.finditer(r"<tr>(.*?)</tr>", tbody, flags=re.S):
        name_m = re.search(r"<td>([^<]*)</td>", m.group(0))
        if name_m:
            rows[name_m.group(1)] = m.group(0)
    assert f"stalled since {_iso(anchor)}" in rows["w1"]
    assert "<td>running</td>" in rows["w1"], "measured state stays"
    assert "stalled since" not in rows["w2"]
    thead = page.split("<thead>")[1].split("</thead>")[0]
    assert thead.count("<th>") == 5, "header keeps its five columns"
    assert page.count("stalled since") == 1, "one row mark on the page"


def test_s124hb_report_strip_and_index_mark(tmp_path: Path) -> None:
    """The campaign strip carries the mark too: a season with a live
    stall names its lane in the cell, on the season page and the index
    alike; a season without an event stays bare."""
    root = _proj(tmp_path)
    _lane(root, "s1", "w1", stalled=True)
    _running_season(root, "s1")
    _lane(root, "s2", "w1", stalled=False)
    _running_season(root, "s2")
    assert loop.run(root, once=True) == 0
    page = report.render_report(root, "s2", tmp_path / "s2.html").read_text(
        encoding="utf-8"
    )
    cells: dict[str, str] = {}
    for m in re.finditer(r'<div class="cell">.*?</div>', page, flags=re.S):
        cell = m.group(0)
        sid_m = re.search(r'<span class="sid">([^<]+)</span>', cell)
        if sid_m:
            cells[sid_m.group(1)] = cell
    assert ">stalled: w1</span>" in cells["s1"]
    assert "stalled" not in cells["s2"], "no event, no mark"
    index = report.render_index(root, tmp_path / "index.html").read_text(
        encoding="utf-8"
    )
    icells: dict[str, str] = {}
    for m in re.finditer(r'<div class="cell">.*?</div>', index, flags=re.S):
        cell = m.group(0)
        sid_m = re.search(r'<span class="sid">([^<]+)</span>', cell)
        if sid_m:
            icells[sid_m.group(1)] = cell
    assert ">stalled: w1</span>" in icells["s1"]
    assert "stalled" not in icells["s2"]


def test_s124hb_report_determinism(tmp_path: Path) -> None:
    """Guard (the M1 contract): with events on the bus, two renders of the
    same persisted bytes stay byte-identical, both surfaces."""
    root = _proj(tmp_path)
    _lane(root, "s1", "w1", stalled=True)
    _running_season(
        root, "s1", agents={"w1": _snap("w1")}
    )
    assert loop.run(root, once=True) == 0
    first = report.render_report(root, "s1", tmp_path / "a.html")
    second = report.render_report(root, "s1", tmp_path / "b.html")
    assert first.read_bytes() == second.read_bytes()
    idxf = report.render_index(root, tmp_path / "ia.html")
    idxs = report.render_index(root, tmp_path / "ib.html")
    assert idxf.read_bytes() == idxs.read_bytes()
