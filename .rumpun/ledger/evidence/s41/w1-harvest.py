"""rumpun harvest — season close into the akar ledger (build order step 4).

`harvest_season` reads the engine's season snapshot and appends one record per
season close: status, duration, per-agent state table, verdict, implies line.
Manual verdict entry first (build order step 4); the body is derived from
harness-observed state only ([H] per P36), never from agent-authored text.

M3 (codex-review-2026-09-14): the close ALSO appends the season-level row to
rimba/<sid>/verdicts.jsonl — the file report and audit already read — so one
harvest call writes both books. band/observed/implies are caller-supplied
verdict content ([A]); the row write itself is harness-side.

M4 full (s41 w1): only terminal seasons harvest. A season whose persisted
status is not completed / failed / stopped_* is refused with AkarError
naming the season and status, before any id is consumed or row written.
The s21 row-exists refusal stays as the second guard behind it.

Write order (s41 w1, the s32 repair): the akar record is appended BEFORE
the verdicts.jsonl season row. A fault after the append but before the row
write leaves the record on the ledger as the recovery source (the row can
be re-added from it); a fault before the append strands nothing, because
the record append is the close's first side effect.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from rumpun import akar, engine, yamlio

logger = logging.getLogger(__name__)

VERDICTS = ("WIN", "LOSS", "NEUTRAL", "INVALID")


def _dash(value: Any) -> str:
    """Markdown cell: None renders as '-', anything else as str()."""
    return "-" if value is None else str(value)


def _render_body(state: dict[str, Any], verdict: str, implies: str) -> str:
    """Record body: season status, duration, agent table, verdict, implies."""
    started = float(state["started_at"])
    ended = state.get("ended_at") or time.time()
    agents = state.get("agents") or {}
    lines = [
        f"season {state['id']}: {state['status']}",
        f"duration: {ended - started:.0f}s",
        "",
        "| agent | route | state | exit_code | seconds |",
        "|---|---|---|---|---|",
    ]
    for name in sorted(agents):
        a = agents[name]
        lines.append(
            f"| {_dash(a.get('name', name))} | {_dash(a.get('route'))}"
            f" | {_dash(a.get('state'))} | {_dash(a.get('exit_code'))}"
            f" | {_dash(a.get('seconds'))} |"
        )
    lines += ["", f"verdict: {verdict}", f"implies: {implies}"]
    return "\n".join(lines)


def _season_metric(root: Path, sid: str) -> str:
    """Campaign metric from musim/<sid>.yaml; '' when the file or key is absent."""
    try:
        cfg = yamlio.load(root / "musim" / f"{sid}.yaml")
    except (OSError, yamlio.YamlError):
        return ""
    value = cfg.get("metric") if isinstance(cfg, dict) else None
    return "" if value is None else str(value)


def _has_season_row(root: Path, sid: str) -> bool:
    """True when rimba/<sid>/verdicts.jsonl already carries a season-level row.

    Corrupt lines are skipped, the same reader contract as report._verdict_of.
    """
    path = root / "rimba" / sid / "verdicts.jsonl"
    if not path.is_file():
        return False
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                if json.loads(line).get("season") == sid:
                    return True
            except ValueError:
                continue
    return False


def _is_terminal(status: str) -> bool:
    """M4: a season is harvestable only once its judgment is final.

    completed, failed, and any stopped_* rule stop are terminal. running
    and any unrecognized status are not: an unrecognized status must fail
    closed, the same stance as engine.status_exit_code, so no unknown
    status consumes the permanent id.
    """
    return status == "completed" or status == "failed" or status.startswith("stopped_")


def harvest_season(
    root: Path,
    sid: str,
    verdict: str,
    implies: str,
    band: str = "",
    observed: str = "",
) -> Path:
    """Close season `sid`: append its akar record AND the season verdict row.

    M4 full: the season's persisted status must be terminal (completed,
    failed, or stopped_*); anything else -- running included -- is refused
    with AkarError naming the season and status, before any id is consumed
    or row written. The s21 refusal (second harvest of a season whose
    verdicts.jsonl already carries the season-level row) stays as the
    second guard. M3: one close writes both books, the akar record and the
    verdicts row; the record is appended FIRST, so a fault between the two
    writes leaves the record as the recovery source and the row re-addable,
    while a fault before it strands nothing. Returns the akar record path.
    """
    if verdict not in VERDICTS:
        msg = f"verdict must be one of {'|'.join(VERDICTS)}, got '{verdict}'"
        raise ValueError(msg)
    state = engine.read_persisted_status(root, sid)
    status = state["status"]
    if not _is_terminal(status):
        msg = (
            f"season {sid} is not terminal (status: {status}); refusing"
            " harvest: only completed, failed, or stopped_* seasons close"
        )
        raise akar.AkarError(msg)
    if _has_season_row(root, sid):
        msg = (
            f"season {sid} is terminal (status: {state['status']}) and"
            f" rimba/{sid}/verdicts.jsonl already carries a season-level"
            " row; refusing second harvest"
        )
        raise akar.AkarError(msg)
    record_id = f"{sid}-harvest"
    body = _render_body(state, verdict, implies)
    # Write order (the s32 repair): the record lands before the row, so a
    # fault after the append leaves the record as the recovery source (the
    # row can be re-added from it) and a fault before the append strands
    # nothing -- the append is the close's first side effect.
    path = akar.append_record(root, record_id, f"season {sid} harvest", body)
    row = {
        "season": sid,
        "verdict": verdict,
        "metric": _season_metric(root, sid),
        "band": band,
        "observed": observed,
        "implies": implies,
    }
    verdicts = root / "rimba" / sid / "verdicts.jsonl"
    verdicts.parent.mkdir(parents=True, exist_ok=True)
    with verdicts.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
        fh.flush()
    logger.info("season %s verdict row appended -> %s", sid, verdicts)
    logger.info("season %s harvested (%s) -> %s", sid, verdict, path)
    return path
