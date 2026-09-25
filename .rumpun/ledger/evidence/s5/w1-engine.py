"""rumpun season engine — spawn, watch, stop (build order step 3).

Port of the kancil supervision pattern (proc.py/swarm.py), fresh code: agents
are one-shot children in their own process groups; the shell wrapper writes an
exit file, so completion is durable and stateless to read. Liveness = pid plus
/proc starttime (PID-reuse guard). Stall = no durable progress (no exit file)
for stall_minutes. No token values ever logged. State writes hold an exclusive
flock on _season/state.lock, so two watchers of one season id serialize
instead of losing updates.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import logging
import os
import signal
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from typing import IO, Any

from rumpun import collab, yamlio

logger = logging.getLogger(__name__)

TERMINAL = {"exited", "failed", "crashed"}


class EngineError(Exception):
    pass


def _proc_start_ticks(pid: int) -> int | None:
    """/proc/<pid>/stat field 22 (starttime), or None if the process is gone."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return None
    tail = stat[stat.rfind(")") + 1:].split()
    if tail and tail[0] == "Z":
        return None  # zombie: dead until reaped, never alive
    # tail[0] is stat field 3 (state); starttime is field 22 -> index 19.
    return int(tail[19]) if len(tail) > 19 else None


def _alive(pid: int, start: int | None) -> bool:
    if start is None:
        return False
    return _proc_start_ticks(pid) == start


def season_dir(root: Path, sid: str) -> Path:
    return root / "rimba" / sid


def state_path(root: Path, sid: str) -> Path:
    return season_dir(root, sid) / "_season" / "state.json"


def _stop_flag(root: Path, sid: str) -> Path:
    return season_dir(root, sid) / "_season" / "stop-flag"


def _load_state(root: Path, sid: str) -> dict[str, Any] | None:
    p = state_path(root, sid)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


@contextlib.contextmanager
def _state_lock(root: Path, sid: str) -> Iterator[IO[str]]:
    """Exclusive flock on _season/state.lock across a state read-modify-write.

    The lock file is opened append-only and never replaced, so concurrent
    processes always flock the same inode; tmp+replace on state.json alone
    prevented torn files but not lost updates (defect spec, s5). flock is per
    open file: a caller already inside this context must pass its lock file to
    _save_state, never re-enter — a second fd would block on itself.
    """
    lock_path = season_dir(root, sid) / "_season" / "state.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    # "a" on the lock recreates it if it vanished and never truncates.
    with open(lock_path, "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield lock_file
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _save_state(
    root: Path, sid: str, state: dict[str, Any], lock_file: IO[str] | None = None,
) -> None:
    """Write state.json atomically under an exclusive flock.

    Single writes flock state.lock here (open, LOCK_EX, write, replace,
    unlock). A caller mid read-modify-write (start_season) passes its held
    lock file so the save joins that cycle instead of flocking a second fd.
    """
    if lock_file is None:
        with _state_lock(root, sid):
            _write_state(root, sid, state)
    else:
        _write_state(root, sid, state)


def _write_state(root: Path, sid: str, state: dict[str, Any]) -> None:
    p = state_path(root, sid)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)  # atomic write


def _stop_rules(season: dict[str, Any]) -> tuple[float, float]:
    """(stall_seconds, budget_seconds) from stop.on plus benih budgets."""
    stall_s = 2700.0  # 45 min default when no stall_minutes rule present
    for rule in season.get("stop", {}).get("on", []):
        if isinstance(rule, dict) and "stall_minutes" in rule:
            stall_s = float(rule["stall_minutes"]) * 60
    minutes = [(b.get("budget") or {}).get("minutes", 0) for b in season["benih"]]
    budget_s = float(max(minutes)) * 60 if minutes else 0.0
    return stall_s, budget_s


def _agent_snap(ws: Path, stall_s: float) -> dict[str, Any]:
    """Recompute one agent's state from disk and /proc. Never mutates."""
    meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    exit_file = ws / "exit"
    code: int | None = None
    if exit_file.is_file():
        with contextlib.suppress(ValueError):
            code = int(exit_file.read_text(encoding="utf-8").strip())
        state = "failed" if code is None else ("exited" if code == 0 else "failed")
    elif (ws / "terminated").is_file():
        state = "terminated"
    elif _alive(meta["pid"], meta["proc_start"]):
        state = "stalled" if time.time() - meta["started_at"] > stall_s else "running"
    else:
        state = "crashed"
    return {
        "name": meta["name"],
        "route": meta.get("route", "?"),
        "state": state,
        "exit_code": code,
        "started_at": meta["started_at"],
        "seconds": round(time.time() - meta["started_at"], 1),
    }


def _agents_snaps(root: Path, sid: str, stall_s: float) -> dict[str, dict[str, Any]]:
    sdir = season_dir(root, sid)
    out: dict[str, dict[str, Any]] = {}
    if not sdir.is_dir():
        return out
    for ws in sorted(sdir.iterdir()):
        if ws.is_dir() and ws.name != "_season" and (ws / "state.json").is_file():
            out[ws.name] = _agent_snap(ws, stall_s)
    return out


def _terminate(ws: Path, pid: int) -> None:
    """SIGTERM the agent's process group, 5s grace, then SIGKILL.

    Writes a terminated marker into the workspace before the first signal so
    later snapshots read "terminated", not "crashed" (defect found in s2,
    patch spec authored by season s4 w1).
    """
    tmp = ws / "terminated.tmp"
    tmp.write_text("terminated\n", encoding="utf-8")
    os.replace(tmp, ws / "terminated")
    with contextlib.suppress(ProcessLookupError):
        os.killpg(pid, signal.SIGTERM)
    deadline = time.time() + 5
    while time.time() < deadline and _proc_start_ticks(pid) is not None:
        time.sleep(0.2)
    with contextlib.suppress(ProcessLookupError):
        os.killpg(pid, signal.SIGKILL)


def _finalize(
    root: Path, sid: str, status: str, snaps: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Kill whatever still runs, record the terminal state. First writer wins."""
    state = _load_state(root, sid) or {}
    if state.get("status", "running") != "running":
        return state
    for aname, meta in state.get("spawned", {}).items():
        snap = snaps.get(aname, {})
        if snap.get("state") in ("running", "stalled"):
            _terminate(season_dir(root, sid) / aname, meta["pid"])
    final_snaps = _agents_snaps(root, sid, 1e9)
    for snap in final_snaps.values():
        if snap["state"] in ("running", "stalled"):
            snap["state"] = "terminated"
    state["agents"] = final_snaps
    state["status"] = status
    state["ended_at"] = time.time()
    _save_state(root, sid, state)
    logger.info("season %s -> %s", sid, status)
    return state


def start_season(yaml_path: Path, root: Path) -> dict[str, Any]:
    """Spawn (or reattach to) a season and watch it to a terminal state."""
    season = yamlio.load(yaml_path)
    sid = str(season["id"])
    cfg = yamlio.load(root / "rumpun.yaml")
    routes: dict[str, str] = cfg.get("routes") or {}
    if not routes:
        msg = "rumpun.yaml routes is empty; run 'rumpun models --write' first"
        raise EngineError(msg)
    stall_s, budget_s = _stop_rules(season)
    # One lock acquisition spans load, the finished check, initial save, and
    # the spawn loop's per-benih saves: a second starter for this sid blocks
    # here, then reads the fully spawned state and reattaches.
    with _state_lock(root, sid) as state_lock:
        state = _load_state(root, sid)
        if state is not None and state.get("status") != "running":
            msg = f"season {sid} already finished ({state.get('status')}); use a fresh id"
            raise EngineError(msg)
        if state is None:
            state = {
                "id": sid, "status": "running", "started_at": time.time(),
                "stall_s": stall_s, "budget_s": budget_s, "spawned": {},
            }
            _save_state(root, sid, state, state_lock)
        spawned: dict[str, Any] = state.setdefault("spawned", {})
        for benih in season["benih"]:
            name = str(benih["name"])
            if name in spawned:
                continue  # reattach: already spawned, keep watching it
            template = routes.get(str(benih["route"]))
            if template is None:
                msg = (
                    f"benih '{name}': route '{benih['route']}' not in rumpun.yaml "
                    "routes; run 'rumpun models --write' first"
                )
                raise EngineError(msg)
            ws = season_dir(root, sid) / name
            ws.mkdir(parents=True, exist_ok=True)
            prompt_src = root / benih["prompt"]
            if not prompt_src.is_file():
                msg = f"benih '{name}': prompt not found: {benih['prompt']}"
                raise EngineError(msg)
            prompt_dest = ws / "prompt.md"
            prompt_dest.write_text(
                prompt_src.read_text(encoding="utf-8"), encoding="utf-8",
            )
            (ws / "prompt-meta.yaml").write_text(
                f"template: {benih['prompt']}\n"
                f"template_sha256: "
                f"{hashlib.sha256(prompt_src.read_bytes()).hexdigest()}\n"
                f"benih: {name}\nroute: {benih['route']}\n",
                encoding="utf-8",
            )
            cmd = template.replace("{prompt}", str(prompt_dest))
            group = benih.get("collab")
            child_env = None
            if group:
                lane = collab.prepare_lane(root, sid, str(group))
                child_env = {
                    **os.environ,
                    "RUMPUN_LANE_FILE": lane["file"],
                    "RUMPUN_LANE_LOCK": lane["lock"],
                }
            exit_file = ws / "exit"
            wrapped = f"{cmd}; __rc=$?; printf '%s' \"$__rc\" > '{exit_file}'"
            with (ws / "agent.log").open("wb") as log_f:
                proc = subprocess.Popen(
                    ["/bin/sh", "-c", wrapped], stdout=log_f, stderr=log_f,
                    env=child_env,
                    start_new_session=True,
                )
            ws_state = {
                "name": name,
                "route": str(benih["route"]),
                "cmd": cmd,
                "pid": proc.pid,
                "proc_start": _proc_start_ticks(proc.pid),
                "started_at": time.time(),
            }
            if group:
                ws_state["collab"] = str(group)
            (ws / "state.json").write_text(
                json.dumps(ws_state, indent=2) + "\n", encoding="utf-8",
            )
            spawned[name] = {
                "pid": proc.pid,
                "proc_start": _proc_start_ticks(proc.pid),
            }
            logger.info("spawned %s (%s) pid %s", name, benih["route"], proc.pid)
            state["spawned"] = spawned
            _save_state(root, sid, state, state_lock)
    while True:
        state = _load_state(root, sid) or state
        if state.get("status") != "running":
            break  # stop_season finalized it underneath us
        snaps = _agents_snaps(root, sid, stall_s)
        states = {s["state"] for s in snaps.values()}
        if states and states <= TERMINAL:
            return _finalize(root, sid, "completed", snaps)
        if any(s["state"] == "stalled" for s in snaps.values()):
            return _finalize(root, sid, "stopped_stall", snaps)
        if budget_s and time.time() - state["started_at"] > budget_s:
            return _finalize(root, sid, "stopped_budget", snaps)
        if _stop_flag(root, sid).exists():
            return _finalize(root, sid, "stopped_operator", snaps)
        time.sleep(1)
    return read_status(root, sid)


def read_status(root: Path, sid: str) -> dict[str, Any]:
    """Live season snapshot (P36 surface 0). Never mutates state."""
    state = _load_state(root, sid)
    if state is None:
        msg = f"no season state for '{sid}'; run 'rumpun season start' first"
        raise EngineError(msg)
    if state["status"] == "running":
        state["agents"] = _agents_snaps(root, sid, float(state.get("stall_s", 2700.0)))
    return state


def stop_season(root: Path, sid: str) -> dict[str, Any]:
    """Operator stop: kill running agents, finalize stopped_operator."""
    state = _load_state(root, sid)
    if state is None:
        msg = f"no season state for '{sid}'"
        raise EngineError(msg)
    if state["status"] != "running":
        return state
    snaps = _agents_snaps(root, sid, float(state.get("stall_s", 2700.0)))
    return _finalize(root, sid, "stopped_operator", snaps)
