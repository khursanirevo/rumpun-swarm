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

s22 (codex-review-2026-09-14 M6): harness fields are authoritative. The
contract is REJECT: a payload carrying a reserved key (seq, from, ts) raises
LaneError and writes nothing. Harness fields are additionally assigned after
payload expansion, so the invariant also holds by construction.

s22 (codex-review-2026-09-14 M7): readers never observe partial rows.
read_events holds LOCK_SH on the lane lock for the whole read; append_event
holds LOCK_EX, writes the row as ONE os.write of the serialized bytes to an
append-mode fd, checks the write was full, and recovers a detected partial
tail — the file lacks a trailing newline AND its last line does not parse as
JSON — by truncating it under the exclusive lock before appending. The
recovery logs the byte count, never the content.
"""

from __future__ import annotations

import fcntl
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

RESERVED_KEYS = ("seq", "from", "ts")


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


def _recover_partial_tail(lane_path: Path) -> int:
    """Truncate a detected partial tail under the held LOCK_EX; return bytes.

    Detected means: the file lacks a trailing newline AND its last line does
    not parse as JSON. A tail whose last line IS valid JSON is left in place
    (per the s22 contract only the invalid-JSON tail is recovered). The log
    carries the recovered byte count only, never the content.
    """
    try:
        data = lane_path.read_bytes()
    except FileNotFoundError:
        return 0  # first use: the append below creates the file
    if not data or data.endswith(b"\n"):
        return 0
    tail = data.rsplit(b"\n", 1)[-1]
    try:
        json.loads(tail)
    except ValueError:
        with open(lane_path, "r+b") as fh:
            fh.truncate(len(data) - len(tail))
        logger.warning("%s: recovered %d bytes of partial tail", lane_path, len(tail))
        return len(tail)
    return 0


def append_event(lane: dict[str, str], sender: str, payload: dict) -> dict:
    """Append one event line under LOCK_EX; seq = count of existing event lines.

    M6 contract: a payload carrying a reserved key (seq, from, ts) raises
    LaneError before the lock and writes nothing. Harness fields (seq, from)
    are assigned after payload expansion, so the caller cannot forge them.
    """
    forged = sorted(set(RESERVED_KEYS).intersection(payload))
    if forged:
        msg = f"payload carries reserved harness keys {forged} from {sender!r}"
        raise LaneError(msg)
    lane_path = Path(lane["file"])
    Path(lane["lock"]).parent.mkdir(parents=True, exist_ok=True)
    # "a" on the lock recreates it if it vanished and never truncates.
    with open(lane["lock"], "a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            _recover_partial_tail(lane_path)
            try:
                with open(lane_path, encoding="utf-8") as fh:
                    seq = sum(1 for line in fh if line.strip())
            except FileNotFoundError:
                seq = 0  # first use: the append below creates the file
            event = {**payload, "seq": seq, "from": sender}
            data = (json.dumps(event, sort_keys=True) + "\n").encode("utf-8")
            fd = os.open(lane_path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
            try:
                if os.write(fd, data) != len(data):
                    msg = f"{lane_path}: short write of {len(data)} bytes"
                    raise LaneError(msg)
            finally:
                os.close(fd)
            logger.debug("appended seq %d from %s to %s", seq, sender, lane_path)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return event


def read_events(lane: dict[str, str]) -> list[dict]:
    """Parse the lane in file order under LOCK_SH; LaneError names the line.

    M7: the shared lock spans the whole read, so a concurrent append (which
    holds LOCK_EX across its single-row write) can never interleave bytes
    into an in-progress read; a reader only ever sees whole rows.
    """
    lane_path = Path(lane["file"])
    Path(lane["lock"]).parent.mkdir(parents=True, exist_ok=True)
    with open(lane["lock"], "a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_SH)
        try:
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
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return events
