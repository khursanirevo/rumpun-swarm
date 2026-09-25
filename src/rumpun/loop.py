"""The campaign loop (#30): event-driven producer/consumer for seasons.

Producers are engine._finalize (season-completed) and harvest_season
(season-harvested): each writes a small JSON event into events/ the
moment its state change commits. The consumer is `rumpun loop`: it
blocks on inotify for zero idle wake-ups, dispatches each event once
(a shell command fed the event JSON on stdin with RUMPUN_EVENT set),
and synthesizes completion events for seasons that terminalized
before the loop ever started, so a restart loses no state change.
Cron keeps only a watchdog role: a second consumer exits 0 at once
on the held loop.lock.
"""

from __future__ import annotations

import fcntl
import json
import logging
import os
import re
import shutil
import struct
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from rumpun import paths

logger = logging.getLogger(__name__)

COMPLETED = "season-completed"
HARVESTED = "season-harvested"
HEARTBEAT = "lane-stalled"

IN_CLOSE_WRITE = 0x8
IN_MOVED_TO = 0x80


def emit_event(root: Path, kind: str, season: str, detail: str) -> Path:
    """Publish one event file atomically; creation order is the bus order."""
    bus = paths.events_dir(root)
    bus.mkdir(parents=True, exist_ok=True)
    path = bus / f"{kind}-{season}.json"
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(
        json.dumps(
            {"kind": kind, "season": season, "detail": detail, "at": time.time()}
        )
        + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)
    logger.info("event emitted: %s", path.name)
    return path


def emit_lane_stalled(
    root: Path, sid: str, lane: str, last_progress: float
) -> Path:
    """Publish one lane-stalled event atomically; one file per lane.

    s124 w1 (the lane heartbeat): re-emission with the same anchor
    writes nothing -- one stall is one event however many ticks it
    survives (idempotent per lane-stall), and a quiet bus stays quiet
    (the watcher wakes on bus writes). A later stall of the same lane
    rewrites the file with the new last-progress anchor.
    """
    bus = paths.events_dir(root)
    bus.mkdir(parents=True, exist_ok=True)
    path = bus / f"{HEARTBEAT}-{sid}-{lane}.json"
    if path.is_file():
        try:
            prior = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            prior = None
        if isinstance(prior, dict) and prior.get("last_progress") == last_progress:
            return path
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(
        json.dumps(
            {
                "kind": HEARTBEAT,
                "season": sid,
                "lane": lane,
                "last_progress": last_progress,
                "at": time.time(),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)
    logger.info("lane-stalled event: %s (last progress %s)", path.name, last_progress)
    return path


def _event_paths(bus: Path) -> list[Path]:
    return sorted(bus.glob("season-*.json"))


def _read_processed(bus: Path) -> set[str]:
    marker = bus / ".processed"
    if not marker.is_file():
        return set()
    return {
        ln.strip()
        for ln in marker.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    }


def _synthesize_missed(root: Path) -> int:
    """Backfill season-completed events for terminal seasons lacking one."""
    from rumpun import engine

    bus = paths.events_dir(root)
    existing = {p.name for p in bus.glob(f"{COMPLETED}-*.json")}
    emitted = 0
    for path in paths.seasons_dir(root).glob("s*.yaml"):
        sid = path.stem
        if f"{COMPLETED}-{sid}.json" in existing:
            continue
        if not engine.state_path(root, sid).is_file():
            continue
        state = engine.read_persisted_status(root, sid)
        if state.get("status") == "running":
            continue
        emit_event(root, COMPLETED, sid, f"synthesized:{state.get('status')}")
        emitted += 1
    if emitted:
        logger.info("synthesized %d missed completion event(s)", emitted)
    return emitted


CLOSE_PREP_RESERVE = (
    "the verdict and the DESIGN entry are reserved to the close worker"
)
CLOSE_PREP_DUTY = (
    "the close worker fills the next season's primary_change and evidence "
    "and launches it; the loop never harvests, seeds, launches, or commits"
)
_DRAFT_SID_RE = re.compile(r"^s(\d+)$")


def _draft_for_close_prep(root: Path, sid: str) -> Path | None:
    """Draft the next season yaml into the finished season's run dir (s120).

    The planner's own draft_next does the drafting: the loop stages a
    byte-identical copy of the parent season plus the real rejected/
    tree under runs/<sid>/seasons/ and calls draft_next rooted at the
    run dir, so the draft lands at runs/<sid>/seasons/s<N+1>.yaml --
    gitignored live state; the tracked seasons/ tree never sees it and
    the worker moves and fills it there. The staged parent is the only
    top-level season and the staged rejected/ copies carry the real
    lifecycle numbers, so the high-water mark matches 'rumpun evolve
    draft' output: a rejected or rolled-back id is never re-issued
    (M8). The record-id leg of the real mark assumes the file/record
    agreement reject_draft and rollback_season enforce by construction.
    The planner's refusals are the verdict: a not-latest parent (the
    planner's own latest-season rule, checked against the real tree)
    or a malformed season returns None and the record seals
    'draft: none'. OSError from staging propagates: a transient copy
    error must not seal a record claiming either way. One draft per
    season: a prior tick's draft in the staging tree is reused.
    Returns the draft path, or None when the planner refused.
    """
    from rumpun import evolve

    match = _DRAFT_SID_RE.match(sid)
    if match is None:
        return None
    real_seasons = paths.seasons_dir(root)
    run_dir = paths.runs_dir(root) / sid
    staging = run_dir / "seasons"
    staged = staging / f"{sid}.yaml"
    drafts = [p for p in staging.glob("s*.yaml") if p.name != staged.name]
    if drafts:
        return drafts[0]
    if evolve._latest_season(real_seasons) != int(match.group(1)):
        # the planner's own precondition: the parent is the latest season
        logger.info("close-prep draft skipped: %s is not the latest season", sid)
        return None
    staging.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(real_seasons / f"{sid}.yaml", staged)
    real_rejected = real_seasons / "rejected"
    if real_rejected.is_dir():
        staged_rejected = staging / "rejected"
        staged_rejected.mkdir(exist_ok=True)
        for entry in real_rejected.iterdir():
            if entry.is_file():
                shutil.copyfile(entry, staged_rejected / entry.name)
    try:
        return evolve.draft_next(run_dir, staged)
    except evolve.EvolveError as exc:
        logger.warning("close-prep draft for %s refused by the planner: %s", sid, exc)
        return None


def _seal_close_prep(root: Path) -> int:
    """Seal one close-prep record per completed season without harvest.

    Directive 17 keeps the close with the close worker: the loop only
    detects the finished season (read_status completed, no <sid>-harvest
    record) and reserves the verdict and the DESIGN entry by name. Since
    s120 the record also carries the next season's draft: the loop runs
    the planner's own draft_next into the season's run dir and names the
    path (draft: none when the planner refuses); the fill-and-launch
    duty stays with the worker, and the loop never harvests, seeds,
    launches, or commits. One record per season: a declared
    <sid>-close-prep id skips the season on every later tick.
    """
    from rumpun import akar, engine

    sealed = 0
    ids = akar.declared_ids(root)
    for path in paths.seasons_dir(root).glob("s*.yaml"):
        sid = path.stem
        if f"{sid}-close-prep" in ids or f"{sid}-harvest" in ids:
            continue
        if not engine.state_path(root, sid).is_file():
            continue
        state = engine.read_status(root, sid)
        if state.get("status") != "completed":
            continue
        ended = state.get("ended_at")
        completed_at = (
            datetime.fromtimestamp(float(ended), tz=timezone.utc).isoformat(
                timespec="seconds"
            )
            if ended is not None
            else "absent"
        )
        try:
            draft = _draft_for_close_prep(root, sid)
        except OSError as exc:
            logger.warning("close-prep draft staging for %s failed: %s", sid, exc)
            continue
        draft_line = f"draft: {draft}" if draft is not None else "draft: none"
        body = "\n".join(
            [
                f"season: {sid}",
                "status: completed",
                f"completed-at: {completed_at}",
                draft_line,
                f"reserve: {CLOSE_PREP_RESERVE}",
                f"fill-and-launch: {CLOSE_PREP_DUTY}",
            ]
        )
        try:
            akar.append_record(
                root, f"{sid}-close-prep", f"season {sid} close prep", body
            )
        except akar.AkarError as exc:
            logger.warning("close-prep seal for %s refused: %s", sid, exc)
            continue
        logger.info("sealed close-prep record for %s (%s)", sid, draft_line)
        sealed += 1
    return sealed


def _lane_heartbeat(root: Path) -> int:
    """s124 w1 (the lane heartbeat): silence becomes an event.

    Each tick scans the running seasons with the engine's own live snap
    reader: a lane past its stall window with no progress -- the snap's
    "stalled" state -- publishes one event per (season, lane) naming
    season, lane, and the last-progress anchor (the workspace
    state.json stamp set: started_at floor, then the durable stamps; a
    lane without stamps floors at started_at). The sweep removes events
    whose lane moved, exited, or whose season stopped, so the bus holds
    exactly the live stalls and the report's marks stay truthful.
    """
    from rumpun import engine

    live: set[tuple[str, str]] = set()
    for path in sorted(paths.seasons_dir(root).glob("s*.yaml")):
        sid = path.stem
        if not engine.state_path(root, sid).is_file():
            continue
        state = engine.read_persisted_status(root, sid)
        if state.get("status") != "running":
            continue
        stall_s = float(state.get("stall_s", 2700.0))
        for lane, snap in engine._agents_snaps(root, sid, stall_s).items():
            if snap.get("state") != "stalled":
                continue
            live.add((sid, lane))
            meta = json.loads(
                (engine.season_dir(root, sid) / lane / "state.json").read_text(
                    encoding="utf-8"
                )
            )
            anchor = float(meta.get("started_at", 0.0))
            for key in ("last_progress", "last_tool_use", "last_ws_progress"):
                if meta.get(key) is not None:
                    anchor = max(anchor, float(meta[key]))
            emit_lane_stalled(root, sid, lane, anchor)
    bus = paths.events_dir(root)
    if bus.is_dir():
        for path in sorted(bus.glob(f"{HEARTBEAT}-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue  # unreadable junk stays; never delete unread files
            key = (
                (payload.get("season"), payload.get("lane"))
                if isinstance(payload, dict)
                else None
            )
            if key not in live:
                path.unlink(missing_ok=True)
    if live:
        logger.info("lane heartbeat: %d stalled lane(s)", len(live))
    return len(live)


def _dispatch(root: Path, event: Path, exec_cmd: str | None) -> int:
    """Hand one event to the exec command (or stdout when no --exec)."""
    payload = event.read_text(encoding="utf-8")
    if exec_cmd is None:
        sys.stdout.write(payload)
        return 0
    env = dict(os.environ, RUMPUN_EVENT=str(event))
    proc = subprocess.run(
        exec_cmd,
        shell=True,
        input=payload,
        env=env,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        logger.error(
            "dispatch rc=%d for %s\nstdout: %s\nstderr: %s",
            proc.returncode,
            event.name,
            proc.stdout[-2000:],
            proc.stderr[-2000:],
        )
    else:
        logger.info("dispatched %s (rc=0)", event.name)
    return proc.returncode


def _drain(root: Path, exec_cmd: str | None) -> int:
    """Dispatch every unseen event once; failures stay for the next startup."""
    bus = paths.events_dir(root)
    bus.mkdir(parents=True, exist_ok=True)
    done = _read_processed(bus)
    failures = 0
    with (bus / ".processed").open("a", encoding="utf-8") as marker:
        for event in _event_paths(bus):
            if event.name in done:
                continue
            if _dispatch(root, event, exec_cmd) == 0:
                marker.write(event.name + "\n")
                marker.flush()
                done.add(event.name)
            else:
                failures += 1
    return failures


def _watch(bus: Path):
    """Yield once per inotify wakeup (a file closes or lands in the bus)."""
    import ctypes

    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.inotify_init()
    if fd < 0:
        raise OSError(ctypes.get_errno(), "inotify_init failed")
    os.set_inheritable(fd, False)
    mask = IN_CLOSE_WRITE | IN_MOVED_TO
    wd = libc.inotify_add_watch(fd, os.fsencode(str(bus)), mask)
    if wd < 0:
        os.close(fd)
        raise OSError(ctypes.get_errno(), f"inotify_add_watch failed for {bus}")
    try:
        while True:
            buf = os.read(fd, 4096)  # blocks until a watched event
            offset = 0
            while offset + 16 <= len(buf):
                _wd, _mask_seen, name_len = struct.unpack_from("iII", buf, offset)
                offset += 16 + name_len
            yield
    finally:
        os.close(fd)


def run(root: Path, exec_cmd: str | None = None, once: bool = False) -> int:
    """The consumer: synthesize, drain, then watch (or exit with --once)."""
    import ctypes

    if not hasattr(ctypes.CDLL(None), "inotify_init"):
        logger.error("rumpun loop needs inotify (Linux); platform lacks it")
        return 2
    lock_path = paths.state_dir(root) / "loop.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("w")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        logger.info("another rumpun loop holds %s; watchdog-safe exit", lock_path)
        handle.close()
        return 0
    from rumpun import engine

    # Issue #33: reap seasons a restart orphaned mid-run before synthesis,
    # so their stopped_restart events join the backlog the drain dispatches.
    engine.recover_orphans(root)
    _synthesize_missed(root)
    _drain(root, exec_cmd)
    _seal_close_prep(root)
    _lane_heartbeat(root)
    if once:
        logger.info("--once: backlog drained, exiting")
        handle.close()
        return 0
    try:
        for _ in _watch(paths.events_dir(root)):
            _drain(root, exec_cmd)
            _seal_close_prep(root)
            _lane_heartbeat(root)
    except KeyboardInterrupt:
        logger.info("rumpun loop stopped by signal")
    handle.close()
    return 0
