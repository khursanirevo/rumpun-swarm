"""rumpun season engine — spawn, watch, stop (build order step 3).

Port of the kancil supervision pattern (proc.py/swarm.py), fresh code: agents
are one-shot children in their own process groups; the shell wrapper writes an
exit file, so completion is durable and stateless to read. Liveness = pid plus
/proc starttime (PID-reuse guard). Stall = no durable progress (no exit file)
for stall_minutes. No token values ever logged. State writes hold an exclusive
flock on _season/state.lock, so two watchers of one season id serialize
instead of losing updates, and _finalize holds that lock across its whole
terminal transaction (terminal check, kill decisions, final write).

Stream tool evidence (s16): fable-route agent.log holds one JSON event per
line (claude stream-json). The engine parses each spawn's stream
incrementally (byte offset tracked as the additive key stream_offset in the
workspace state.json), marks file_tools=true at the first parsed file-tool
name, and at finalize marks file_tools=false only when the stream held at
least one parseable event and never a file-tool name. Logs carry event
types, tool names, byte counts, paths -- never stream content or token
values.
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


# --- stream tool evidence (s16) ------------------------------------------
# Positive set: a name outside FILE_TOOLS (ToolSearch, WebFetch, Task, and
# Agent-class spawn names included) never counts as a file tool.
FILE_TOOLS = frozenset(
    {"Read", "Write", "Edit", "Bash", "Grep", "Glob", "NotebookEdit"}
)


def _parse_stream_events(text: str) -> Iterator[dict[str, Any]]:
    """Yield parseable dict events from a stream-json text, line by line.

    Lines split on "\n" only: a JSON string may legally contain U+2028 and
    friends, which str.splitlines would treat as line breaks, so splitlines
    is avoided. Blank lines are skipped silently. Malformed lines are
    skipped from classification with one DEBUG each (byte count only, never
    content). Parseable non-dict JSON lines are skipped silently (an event
    is an object in this stream format).
    """
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            logger.debug(
                "stream line skipped from classification (malformed, %d bytes)",
                len(line),
            )
            continue
        if isinstance(event, dict):
            yield event


def _tool_names(event: dict[str, Any]) -> Iterator[str]:
    """Tool names from tool_use blocks in one event's message.content array.

    The stream-json producer puts tool_use blocks with a name inside
    assistant message content arrays; collection keys off the block shape,
    not the top-level event type (in practice only assistant messages carry
    tool_use blocks).
    """
    message = event.get("message")
    if not isinstance(message, dict):
        return
    content = message.get("content")
    if not isinstance(content, list):
        return
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            name = block.get("name")
            if isinstance(name, str) and name:
                yield name


def stream_tool_names(text: str) -> set[str]:
    """Tool names from a stream-json text (pure; the s15 classifier contract).

    Parses each line with json.loads and collects every tool name from
    tool_use blocks in assistant message content arrays. Malformed lines:
    skipped from classification, one DEBUG each. Empty text -> empty set.
    Never returns or logs stream content or token values.
    """
    return {
        name
        for event in _parse_stream_events(text)
        for name in _tool_names(event)
    }


def _write_agent_state(ws: Path, meta: dict[str, Any]) -> None:
    """Atomically rewrite one workspace's state.json (tmp + replace)."""
    tmp = (ws / "state.json").with_suffix(".tmp")
    tmp.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    tmp.replace(ws / "state.json")


def _write_agent_state_guarded(
    root: Path, sid: str, ws: Path, meta: dict[str, Any],
    lock_file: IO[str] | None,
) -> None:
    """Workspace state write under the season lock: join a held lock or derive one.

    Mirrors _save_state: a caller mid-transaction passes its held lock file;
    flock is per open file, so deriving a second fd while holding the lock
    would block on itself.
    """
    if lock_file is None:
        with _state_lock(root, sid):
            _write_agent_state(ws, meta)
    else:
        _write_agent_state(ws, meta)


def _root_sid(ws: Path) -> tuple[Path, str]:
    """(root, sid) for a workspace path under the fixed rimba layout.

    ws = root/rimba/<sid>/<name>; the stream helpers derive the season
    state lock from it so _scan_agent_stream keeps its (ws, meta) shape.
    """
    return ws.parents[2], ws.parent.name


def _mark_file_tools(
    root: Path, sid: str, ws: Path, meta: dict[str, Any], tool: str,
) -> None:
    """The one-time file-tool mark: WARNING (path + tool name) + one lane event.

    Called only on the true transition; true is sticky, so this never
    repeats. The lane event carries event type, agent, tool name, byte count
    -- never stream content or token values.
    """
    logger.warning("%s: file tool '%s' in spawn stream", ws / "agent.log", tool)
    group = meta.get("collab")
    if not group:
        return
    lane = collab.prepare_lane(root, sid, str(group))
    collab.append_event(
        lane,
        "engine",
        {
            "type": "file_tools",
            "agent": str(meta.get("name", ws.name)),
            "tool": tool,
            "bytes": int(meta.get("stream_offset", 0)),
        },
    )


def _scan_agent_stream(ws: Path, meta: dict[str, Any]) -> None:
    """Consume agent.log bytes appended past meta's stream_offset, one agent.

    Only complete lines (through the last newline) are consumed; a trailing
    partial line waits for its newline. The offset lives as the additive
    key stream_offset in the workspace state.json and always advances to
    the consumed end. file_tools=true is sticky: once set it is never
    re-evaluated or unset, but scanning continues so the offset stays
    exact and the size == offset skip stays sound. The write goes
    through the season state flock, derived from ws (root/rimba/<sid>/<name>);
    never call while already holding that lock (flock is per open file: a
    second fd would block on itself). Concurrent scans converge: equal
    starting offsets parse equal bytes, so both compute the same meta. The
    WARNING and lane event fire only on the false->true transition (s17 live
    defect: one WARNING per sighting); the offset advance and the sticky
    mark stay per-sighting.
    """
    log_path = ws / "agent.log"
    try:
        size = log_path.stat().st_size
    except OSError:
        return
    offset = int(meta.get("stream_offset", 0))
    if size < offset:
        offset = 0  # log shrank: append-only was violated, rescan from start
    if size == offset:
        return
    with log_path.open("rb") as fh:
        fh.seek(offset)
        chunk = fh.read(size - offset)
    cut = chunk.rfind(b"\n")
    if cut < 0:
        return  # no complete line yet; the partial line stays unconsumed
    root, sid = _root_sid(ws)
    meta["stream_offset"] = offset + cut + 1
    names = stream_tool_names(chunk[: cut + 1].decode("utf-8", errors="replace"))
    found = sorted(names & FILE_TOOLS)
    if found:
        # The alert (WARNING + lane event) is transition-gated (s17 live
        # defect: one WARNING per sighting); the sticky mark and the offset
        # advance stay per-sighting.
        first_mark = meta.get("file_tools") is not True
        meta["file_tools"] = True
        if first_mark:
            _mark_file_tools(root, sid, ws, meta, found[0])
    with _state_lock(root, sid):
        _write_agent_state(ws, meta)


def _finalize_agent_stream(
    root: Path, sid: str, ws: Path, lock_file: IO[str] | None = None,
) -> None:
    """Terminal classification for one workspace (called from _finalize).

    file_tools=true wins (sticky, early return). Otherwise the whole
    stream is classified once, regardless of watcher history (reattach,
    watcher crash, cold stop): any file-tool name -> true; at least one
    parseable event and none -> false; zero parseable events -> the key
    stays absent (never guessed from an empty or text-only stream). One
    terminal full read per workspace; the watcher cycle never re-reads
    consumed bytes. The write goes through the season state flock: pass a
    held lock file (the _finalize transaction) or the call derives its own;
    never re-enter while already holding that lock (a second fd would
    block on itself).
    """
    meta_path = ws / "state.json"
    if not meta_path.is_file():
        return
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("file_tools") is True:
        return
    log_path = ws / "agent.log"
    try:
        size = log_path.stat().st_size
    except OSError:
        return
    text = log_path.read_text(encoding="utf-8", errors="replace")
    events = 0
    file_tool: str | None = None
    for event in _parse_stream_events(text):
        events += 1
        if file_tool is None:
            file_tool = next(
                (n for n in _tool_names(event) if n in FILE_TOOLS), None
            )
    if file_tool is not None:
        meta["file_tools"] = True
        meta["stream_offset"] = size
        _mark_file_tools(root, sid, ws, meta, file_tool)
        _write_agent_state_guarded(root, sid, ws, meta, lock_file)
    elif events >= 1:
        meta["file_tools"] = False
        meta["stream_offset"] = size
        _write_agent_state_guarded(root, sid, ws, meta, lock_file)
    # events == 0 (or log missing): file_tools stays absent -- never guessed.


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
        last_progress = meta["started_at"]
        with contextlib.suppress(OSError):
            last_progress = max(last_progress, (ws / "agent.log").stat().st_mtime)
        state = (
            "stalled" if time.time() - last_progress > stall_s else "running"
        )
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
    """Kill whatever still runs, record the terminal state. First writer wins.

    H1 (codex-review-2026-09-14): one exclusive flock on _season/state.lock
    spans the whole transaction -- terminal-state check, ownership snapshot,
    termination, and the final write (the held lock file joins _save_state).
    Unlocked, a stop racing start_season's spawn loop finalized from a stale
    read: the held spawn landed in a season the stop had already closed,
    live and untracked (review reproduction). The pre-lock read is advisory;
    the check repeats under the lock. Kill decisions use a fresh liveness
    snapshot taken under the lock: the caller's snaps predate the lock wait
    and cannot see agents admitted meanwhile (the review repro's second
    benih). The snaps argument stays for caller-signature stability only.
    _finalize_agent_stream joins the held lock instead of deriving its own
    (flock is per open file: a second fd would block on itself).
    """
    state = _load_state(root, sid) or {}
    if state.get("status", "running") != "running":
        return state
    with _state_lock(root, sid) as state_lock:
        state = _load_state(root, sid) or {}
        if state.get("status", "running") != "running":
            return state
        # Ownership + liveness snapshot under the lock (pre-kill): a stop
        # that waited on the spawn loop sees agents the caller's snaps miss.
        live = _agents_snaps(root, sid, 1e9)
        for aname, meta in state.get("spawned", {}).items():
            if live.get(aname, {}).get("state") in ("running", "stalled"):
                _terminate(season_dir(root, sid) / aname, meta["pid"])
        final_snaps = _agents_snaps(root, sid, 1e9)
        for aname in state.get("spawned", {}):
            _finalize_agent_stream(
                root, sid, season_dir(root, sid) / aname, state_lock,
            )
        for aname, snap in final_snaps.items():
            meta_path = season_dir(root, sid) / aname / "state.json"
            if not meta_path.is_file():
                continue  # crashed before first write; nothing to merge
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            for key in ("file_tools", "stream_offset"):
                if key in meta:
                    snap[key] = meta[key]
        for snap in final_snaps.values():
            if snap["state"] in ("running", "stalled"):
                snap["state"] = "terminated"
        state["agents"] = final_snaps
        state["status"] = status
        state["ended_at"] = time.time()
        _save_state(root, sid, state, state_lock)
    logger.info("season %s -> %s", sid, status)
    return state


_STRIP_CHILD = (
    "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_FABLE_MODEL",
)


def _child_env(root: Path, sid: str, group: Any) -> dict[str, str]:
    """Child env: parent env minus model-suffix vars, plus lane vars for the group.

    Spawned sessions inherit model env with a [1m] context suffix (for example
    glm-5.2[1m]); the relay maps suffixed sessions to a degraded toolset --
    4 of 16 spawns came up with no file/exec tools (akar glm-toolless-spawn).
    Stripping the suffix vars lets the child resolve its own model. Collab
    groups additionally get the lane env vars.
    """
    env = {k: v for k, v in os.environ.items() if k not in _STRIP_CHILD}
    if group:
        lane = collab.prepare_lane(root, sid, str(group))
        env["RUMPUN_LANE_FILE"] = lane["file"]
        env["RUMPUN_LANE_LOCK"] = lane["lock"]
    return env


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
            child_env = _child_env(root, sid, benih.get("collab"))
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
            if benih.get("collab"):
                ws_state["collab"] = str(benih["collab"])
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
        # Stream tool evidence: one scan per live agent per existing cycle.
        # _scan skips agents already marked, at EOF, or without a complete
        # line; terminal agents classify once at finalize.
        for aname, snap in snaps.items():
            if snap["state"] not in ("running", "stalled"):
                continue
            ws = season_dir(root, sid) / aname
            meta_path = ws / "state.json"
            if not meta_path.is_file():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            _scan_agent_stream(ws, meta)
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
