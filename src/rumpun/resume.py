"""rumpun resume (#27): the one-screen operator re-entry view.

resume.md re-derives from on-disk state at every season close and on
every `rumpun resume` call: the newest closed season with its verdict
and implication, the running seasons with their agents, pending
operator directives, the newest audit candidates, and the evidence
paths. It is a derived view with no new primary state, atomically
rewritten, so the "return after absence" question is one file read.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import date
from pathlib import Path

from rumpun import akar, collab, engine, kanban, paths

logger = logging.getLogger(__name__)

_SEASON_ID = re.compile(r"s\d+")


def _verdict_row(root: Path, sid: str) -> dict | None:
    """The season-level verdict row for sid (agent rows carry no verdict)."""
    path = paths.runs_new(root) / sid / "verdicts.jsonl"
    if not path.is_file():
        return None
    row = None
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except ValueError:
                continue
            if isinstance(parsed, dict) and "verdict" in parsed:
                row = parsed
    return row


def _newest_closed(root: Path) -> tuple[str, dict] | None:
    """(sid, state) of the highest-numbered season in a non-running state."""
    best: tuple[int, str, dict] | None = None
    for path in paths.seasons_dir(root).glob("s*.yaml"):
        sid = path.stem
        if not engine.state_path(root, sid).is_file():
            continue
        state = engine.read_persisted_status(root, sid)
        if state.get("status") == "running":
            continue
        num = kanban._season_num(sid)
        if num >= 0 and (best is None or num > best[0]):
            best = (num, sid, state)
    if best is None:
        return None
    return best[1], best[2]


def _pending_directives(root: Path) -> list[str]:
    """Unshipped operator directives, as seq + text lines."""
    ledger = paths.ledger_dir(root)
    lane_file = ledger / "directives.jsonl"
    if not lane_file.is_file():
        return []
    lane = {"file": str(lane_file), "lock": str(ledger / "directives.lock")}
    entries = []
    for event in collab.read_events(lane):
        if event.get("status") != "pending":
            continue
        text = event.get("text") or event.get("directive") or ""
        entries.append(f"seq {event.get('seq', '?')}: {text}")
    return entries


def render(root: Path) -> str:
    """The resume text: newest close, running, pending, audit, evidence."""
    lines = [f"# campaign resume ({date.today().isoformat()})", ""]

    lines += ["## Newest closed season"]
    closed = _newest_closed(root)
    if closed is None:
        lines.append("- none closed yet")
    else:
        sid, state = closed
        row = _verdict_row(root, sid) or {}
        ledger = akar.declared_ids(root).get(f"{sid}-harvest")
        lines.append(
            f"- {sid}: {state.get('status')},"
            f" verdict {row.get('verdict', 'no verdict row')},"
            f" implies: {row.get('implies') or '-'}"
        )
        lines.append(f"- harvest record: {ledger or 'none on the ledger'}")
        lines.append(f"- evidence: {paths.runs_new(root) / sid / 'verdicts.jsonl'}")
    lines.append("")

    lines += ["## Running"]
    doing = kanban._doing_cards(root)
    lines += [f"- {card}" for card in doing] or ["- nothing running"]
    lines.append("")

    lines += ["## Pending directives"]
    pending = _pending_directives(root)
    lines += [f"- {entry}" for entry in pending] or ["- none"]
    lines.append("")

    lines += ["## Newest audit"]
    audit_rid, candidates = kanban._latest_audit(root)
    if audit_rid:
        lines.append(f"- {audit_rid}")
        lines += [f"- {candidate}" for candidate in candidates[:3]]
    else:
        lines.append("- none on the ledger")
    lines.append("")
    return "\n".join(lines) + "\n"


def write_resume(root: Path) -> Path:
    """Atomically rewrite resume.md and return its path."""
    path = paths.state_dir(root) / "resume.md"
    tmp = path.with_name(".resume.md.tmp")
    tmp.write_text(render(root), encoding="utf-8")
    os.replace(tmp, path)
    logger.info("resume written -> %s", path)
    return path
