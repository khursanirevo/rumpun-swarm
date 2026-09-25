"""rumpun epics — the epic declaration and the rollup verb (s58; directive seq 5).

Seasons group into epics as DATA (operator directive seq 5, 2026-09-16): one
campaign-level declaration, .rumpun/epics.yaml, maps an epic id to {title,
goal, seasons: [...]}, and `rumpun epics` renders one line per epic — id, the
member seasons' span, the verdict rollup (X WIN / Y LOSS / Z other), and the
title. A member with no run state is marked on the line, never counted or
guessed. The rollup reads the harvest verdict rows (runs/<sid>/verdicts.jsonl,
the last row naming the season wins) and the runs state (the engine's
persisted-status contract: a missing state.json is the EngineError case
'season list' already handles). The ledger is never written by this feature:
declaration plus read-only views, append-only preserved.

--init scaffolds epics.yaml from the season yamls: one 'campaign' epic holding
every season id in numeric order, title and goal from the campaign rumpun.yaml
(falls back to the epic id and an empty goal). It refuses to overwrite an
existing declaration.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

from rumpun import engine, paths, yamlio

logger = logging.getLogger(__name__)

EPICS_FILENAME = "epics.yaml"
CAMPAIGN_EPIC_ID = "campaign"


class EpicsError(Exception):
    pass


def epics_path(root: Path) -> Path:
    """The declaration file inside the .rumpun root (root IS .rumpun)."""
    return root / EPICS_FILENAME


def _season_num(sid: str) -> tuple[int, str]:
    m = re.fullmatch(r"s(\d+)", sid)
    return (int(m.group(1)) if m else 0, sid)


def season_ids(root: Path) -> list[str]:
    """Season yaml ids, in numeric order (s<N> first by number, then stems)."""
    out: list[tuple[int, str]] = []
    for path in sorted(paths.seasons_dir(root).glob("s*.yaml")):
        sid = str(yamlio.load(path).get("id") or path.stem)
        out.append(_season_num(sid))
    return [sid for _, sid in sorted(out)]


def scaffold(root: Path) -> dict[str, Any]:
    """The --init document: one campaign epic over every season yaml id."""
    title, goal = CAMPAIGN_EPIC_ID, ""
    try:
        campaign = yamlio.load(root / "rumpun.yaml").get("campaign") or {}
        if isinstance(campaign, dict):
            title = str(campaign.get("title") or CAMPAIGN_EPIC_ID)
            goal = str(campaign.get("goal") or "")
    except yamlio.YamlError:
        logger.warning("rumpun.yaml unreadable; scaffolding with an empty goal")
    return {
        CAMPAIGN_EPIC_ID: {"title": title, "goal": goal, "seasons": season_ids(root)}
    }


def init(root: Path) -> Path:
    """Write the scaffold to .rumpun/epics.yaml (atomic; never overwrites)."""
    target = epics_path(root)
    if target.exists():
        msg = f"{target} already exists; --init never overwrites a declaration"
        raise EpicsError(msg)
    doc = scaffold(root)
    tmp = target.with_name(EPICS_FILENAME + ".tmp")
    tmp.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    tmp.replace(target)
    members = doc[CAMPAIGN_EPIC_ID]["seasons"]
    logger.info(
        "scaffolded %s: 1 epic (%s), %d season(s)",
        target, CAMPAIGN_EPIC_ID, len(members),
    )
    return target


def has_run_state(root: Path, sid: str) -> bool:
    """Runs-state presence per the engine's persisted-status contract."""
    try:
        engine.read_persisted_status(root, sid)
    except engine.EngineError:
        return False
    return True


def season_verdict(root: Path, sid: str) -> str | None:
    """The harvest verdict: the LAST verdicts.jsonl row naming sid; None when
    the season has no verdict row (never harvested, or the row names another
    season). A read error propagates: a corrupt verdict file is a real error.
    """
    path = paths.runs_dir(root) / sid / "verdicts.jsonl"
    if not path.is_file():
        return None
    verdict: str | None = None
    with path.open(encoding="utf-8") as fh:
        for row_line in fh:
            if not row_line.strip():
                continue
            row = json.loads(row_line)
            if str(row.get("season")) == sid:
                verdict = str(row.get("verdict") or "")
    return verdict or None


def render(root: Path) -> list[str]:
    """One line per epic, in declaration order.

    `{id}  {span}  {W} WIN / {L} LOSS / {O} other  {title}` with a trailing
    `(no run state: <ids>)` when a member has no runs state. The span is the
    numeric first-last of the member ids. Counts: WIN/LOSS verdicts exactly;
    `other` absorbs NEUTRAL/INVALID verdicts AND members with run state but
    no verdict row (an honest unknown, named here rather than guessed). A
    no-run-state member is excluded from the counts and marked on the line.
    """
    doc = yamlio.load(epics_path(root))
    if not isinstance(doc, dict):
        msg = f"{epics_path(root)}: the epics document must be a mapping"
        raise EpicsError(msg)
    lines: list[str] = []
    for epic_id, body in doc.items():
        if not isinstance(body, dict):
            msg = f"epic '{epic_id}': declaration must be a mapping"
            raise EpicsError(msg)
        members = sorted((str(m) for m in body.get("seasons") or []), key=_season_num)
        span = members[0] if len(members) == 1 else f"{members[0]}-{members[-1]}"
        wins = losses = others = 0
        no_state: list[str] = []
        for sid in members:
            verdict = season_verdict(root, sid)
            if verdict is None and not has_run_state(root, sid):
                no_state.append(sid)
                continue
            if verdict == "WIN":
                wins += 1
            elif verdict == "LOSS":
                losses += 1
            else:
                others += 1
        title = str(body.get("title") or epic_id)
        row = f"{epic_id}  {span}  {wins} WIN / {losses} LOSS / {others} other  {title}"
        if no_state:
            row += f"  (no run state: {', '.join(no_state)})"
        lines.append(row)
    return lines
