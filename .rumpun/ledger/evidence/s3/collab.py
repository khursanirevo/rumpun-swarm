"""Collab lanes — one shared JSONL event log per collab group.

Benih run in separate workspaces (fight mode), so a collab group gets its
coordination medium as files: prepare_lane creates the lane (events) + lock
pair under the season dir and the engine exports the paths as
RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK. Agents only append; read_events replays
the lane in file order. append_event is read-then-append — count event lines
for the next seq, write exactly one line — under an exclusive flock on the
lock file, so concurrent appenders serialize and seq stays dense and unique.
Existing files are never truncated: a late joiner or an engine restart must
not eat history. Stdlib-only, Linux-only (fcntl); no clock reads, no
randomness — the lane is the record.
"""

from __future__ import annotations

import fcntl
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LaneError(Exception):
    pass


def prepare_lane(root: Path, sid: str, group: str) -> dict[str, str]:
    """Create the lane + lock pair if missing; never truncate; return abs paths."""
    season = root / "rimba" / sid / "_season"
    season.mkdir(parents=True, exist_ok=True)
    lane_file = season / f"lane-{group}.jsonl"
    lock_file = season / f"lane-{group}.lock"
    for path in (lane_file, lock_file):
        path.touch(exist_ok=True)
    return {"file": str(lane_file.resolve()), "lock": str(lock_file.resolve())}


def append_event(lane: dict[str, str], sender: str, payload: dict) -> dict:
    """Append one event line under LOCK_EX; seq = count of existing event lines."""
    lane_path = Path(lane["file"])
    # "a" on the lock recreates it if it vanished and never truncates.
    with open(lane["lock"], "a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            with open(lane_path, encoding="utf-8") as fh:
                seq = sum(1 for line in fh if line.strip())
            event = {"seq": seq, "from": sender, **payload}
            with open(lane_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, sort_keys=True) + "\n")
            logger.debug("appended seq %d from %s to %s", seq, sender, lane_path)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return event


def read_events(lane: dict[str, str]) -> list[dict]:
    """Parse the lane in file order, skipping blank lines; LaneError names the line."""
    lane_path = Path(lane["file"])
    events: list[dict] = []
    with open(lane_path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                msg = f"{lane_path}: line {lineno} is not valid JSON: {exc}"
                raise LaneError(msg) from exc
    return events
