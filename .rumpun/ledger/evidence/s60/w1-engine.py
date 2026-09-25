"""rumpun season engine — spawn, watch, stop (build order step 3).

Port of the kancil supervision pattern (proc.py/swarm.py), fresh code: agents
are one-shot children in their own process groups, spawned with cwd set to
their resolved workspace (H3, codex-review-2026-09-14); the shell wrapper
writes an exit file, so completion is durable and stateless to read. Liveness = pid plus
/proc starttime (PID-reuse guard). Stall = no durable progress (no exit file)
for stall_minutes. Progress is content-based (s24): the watcher tracks each
live agent's last-seen agent.log byte size; only growth counts, mtime-only
touches do not. s60 widens the rule -- the s59 kill terminated w2 mid-write
(stdout quiet, files busy on a 274-line pins file): any parsed tool_use
event and observed workspace write growth reset the stall clock too. No
token values ever logged. State writes hold an exclusive
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
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import IO, Any

from rumpun import collab, paths, yamlio

logger = logging.getLogger(__name__)

TERMINAL = {"exited", "failed", "crashed"}

state_hook: Callable[[], None] | None = None
"""Called once per watcher cycle while a season runs (render refresh).

Set by the CLI (index re-render); engine never imports report. A failing
hook is logged and ignored: it can never kill a watcher.
"""


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
    """(root, sid) for a workspace path under the fixed runs/ layout.

    ws = root/<runs|rimba>/<sid>/<name>; the stream helpers derive the season
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
    through the season state flock, derived from ws (root/<runs|rimba>/<sid>/<name>);
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
    consumed_to = offset + cut + 1
    prev_size = meta.get("log_size")
    if prev_size is not None and consumed_to > int(prev_size):
        meta["last_progress"] = time.time()
    meta["log_size"] = consumed_to
    meta["stream_offset"] = consumed_to
    names = stream_tool_names(chunk[: cut + 1].decode("utf-8", errors="replace"))
    if names:
        # s60 w1: any parsed tool_use event is durable progress, whatever
        # the tool class. The count is stop-record evidence; the stamp
        # gates the clock. An append-only rescan (shrunken log) may
        # double-count; the stamp stays per-sighting and exact.
        meta["last_tool_use"] = time.time()
        meta["tool_use_count"] = int(meta.get("tool_use_count", 0)) + len(names)
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


# s60 w1 file-tool progress: engine bookkeeping files at a workspace root.
# They mutate for reasons other than agent file-tool work (the scan rewrites
# state.json whenever it advances; the shell wrapper writes exit), so they
# never count as watched writes. Root-level names only: agent-written files
# named alike in deeper scratch trees still count.
_BOOKKEEPING = frozenset(
    {"agent.log", "state.json", "state.json.tmp", "exit", "terminated", "terminated.tmp"}
)


def _watched_bytes(ws: Path) -> int:
    """Content bytes under one workspace, engine bookkeeping excluded.

    Recursive size sum over regular files. Symlinks are never counted and
    never followed, so a symlinked tree cannot smuggle in external content
    or a self-referential loop. Unreadable entries contribute zero: the sum
    undercounts rather than raising, because a stat miss must never kill a
    watcher cycle.
    """
    total = 0
    stack = [ws]
    while stack:
        try:
            with os.scandir(stack.pop()) as it:
                entries = list(it)
        except OSError:
            continue
        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    stack.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    if os.path.dirname(entry.path) == str(ws) and entry.name in _BOOKKEEPING:
                        continue
                    total += entry.stat(follow_symlinks=False).st_size
            except OSError:
                continue
    return total


def _scan_agent_writes(ws: Path, meta: dict[str, Any]) -> None:
    """s60 w1: watch one agent's workspace for file-tool write growth.

    The s59 kill shipped because the stall clock keyed only on agent.log
    appended-byte growth: a writer quiet on stdout while busy on files (w2,
    mid-write on a 274-line pins file) aged out and was terminated. Watched
    workspace writes are the second durable-progress surface: the recursive
    content-byte sum from _watched_bytes against the baseline in meta. The
    first sighting sets the ws_bytes baseline (no stamp); growth past it
    stamps last_ws_progress and refreshes the baseline; shrink or same-size
    rewrite stamps nothing (growth-only, the s24 honesty trade-off: content
    must grow, mtime is never consulted). Only a changed meta is written,
    through the season state flock derived from ws -- never call while
    already holding that lock (a second fd would block on itself). A write
    driven by something other than the agent stamps too: the rule keys on
    harness-observed durable progress, not authorship (the same residual
    holds today for an operator appending to agent.log).
    """
    total = _watched_bytes(ws)
    if "ws_bytes" not in meta:
        meta["ws_bytes"] = total
    elif total > int(meta["ws_bytes"]):
        meta["ws_bytes"] = total
        meta["last_ws_progress"] = time.time()
    else:
        return
    root, sid = _root_sid(ws)
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
    return paths.runs_dir(root) / sid


def state_path(root: Path, sid: str) -> Path:
    return season_dir(root, sid) / "_season" / "state.json"


def _stop_flag(root: Path, sid: str) -> Path:
    return season_dir(root, sid) / "_season" / "stop-flag"


def _load_state(root: Path, sid: str) -> dict[str, Any] | None:
    p = state_path(root, sid)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _state_digest(root: Path, sid: str) -> bytes:
    """sha256 digest of the persisted state.json bytes (s31 w1 gate).

    The watcher hashes the same file _load_state reads; the digest gates
    the state_hook render: identical persisted bytes never re-render. The
    s30 launch re-rendered an identical index once per cycle (~1600 renders
    for one season, audit-19 evidence).
    """
    return hashlib.sha256(state_path(root, sid).read_bytes()).digest()


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


def _writer_table(season: dict[str, Any]) -> list[dict[str, Any]]:
    """The season's writer table: writers (current) or benih (the alias)."""
    return season.get("writers") or season.get("benih") or []


def _stop_rules(season: dict[str, Any]) -> tuple[float, float]:
    """(stall_seconds, budget_seconds) from stop.on plus benih budgets."""
    stall_s = 2700.0  # 45 min default when no stall_minutes rule present
    for rule in season.get("stop", {}).get("on", []):
        if isinstance(rule, dict) and "stall_minutes" in rule:
            stall_s = float(rule["stall_minutes"]) * 60
    minutes = [(b.get("budget") or {}).get("minutes", 0) for b in _writer_table(season)]
    budget_s = float(max(minutes)) * 60 if minutes else 0.0
    return stall_s, budget_s


def _agent_snap(
    ws: Path, stall_s: float,
    last_size: int | None = None, last_progress: float | None = None,
) -> dict[str, Any]:
    """Recompute one agent's state from disk and /proc. Never mutates.

    Content-based stall progress (s24, closes the M10 trade-off): the
    watcher passes its per-agent history -- last_size, the agent.log byte
    size seen on the previous cycle, and last_progress, the time that size
    last grew. Growth past last_size is durable progress; an unchanged size
    provides none regardless of mtime, so touching the log without
    appending no longer defeats stall detection (akar
    stall-rule-fired-on-runtime). last_size=None (first cycle, reattach,
    or a history-less caller such as read_status) keeps the s15 mtime
    estimate; a missing or unreadable log floors at started_at.
    """
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
        last = meta["started_at"]  # floor: no log (yet)
        try:
            st = (ws / "agent.log").stat()
        except OSError:
            st = None
        if st is not None:
            if "log_size" in meta:
                # Scan-stamped content truth (s24 pin contract): once a
                # scan baseline exists, mtime is not consulted; progress
                # is the last growth stamp (none -> started_at floor).
                last = max(
                    last,
                    float(meta.get("last_progress") or meta["started_at"]),
                )
            elif last_size is None:
                # No cross-cycle size history: the s15 mtime estimate (the
                # M10 pin contract for single-shot callers).
                last = max(last, st.st_mtime)
            elif st.st_size > last_size:
                last = time.time()  # appended bytes: durable progress now
            elif last_progress is not None:
                last = max(last, last_progress)  # quiet: hold at last growth
        # s60 w1 (file-tool progress): parsed tool_use events and observed
        # workspace write growth reset the stall clock too -- the s59 kill:
        # stdout quiet, files busy. Absent stamps change nothing: a dead
        # stream with no events and no watched writes still floors at
        # started_at, so genuine liveness is not weakened.
        for key in ("last_tool_use", "last_ws_progress"):
            stamp = meta.get(key)
            if stamp is not None:
                last = max(last, float(stamp))
        state = (
            "stalled" if time.time() - last > stall_s else "running"
        )
    else:
        state = "crashed"
    snap = {
        "name": meta["name"],
        "route": meta.get("route", "?"),
        "state": state,
        "exit_code": code,
        "started_at": meta["started_at"],
        "seconds": round(time.time() - meta["started_at"], 1),
    }
    # H9 (codex-review-2026-09-14): budget-stopped agents keep state
    # "terminated"; the additive key records the reason.
    if state == "terminated" and meta.get("terminated_budget"):
        snap["terminated_budget"] = True
    return snap


def _agents_snaps(
    root: Path, sid: str, stall_s: float,
    log_hist: dict[str, tuple[int, float]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Per-agent snaps; log_hist carries the watcher's content history.

    log_hist maps agent name -> (last-seen agent.log byte size, time that
    size last grew); names missing from it are history-less (mtime estimate).
    """
    sdir = season_dir(root, sid)
    out: dict[str, dict[str, Any]] = {}
    if not sdir.is_dir():
        return out
    for ws in sorted(sdir.iterdir()):
        if ws.is_dir() and ws.name != "_season" and (ws / "state.json").is_file():
            size, grew_at = (log_hist or {}).get(ws.name, (None, None))
            out[ws.name] = _agent_snap(ws, stall_s, size, grew_at)
    return out


def _terminate(ws: Path, pid: int, proc_start: int | None) -> None:
    """SIGTERM the agent's process group, 5s grace, then SIGKILL.

    H2 (codex-review-2026-09-14): the caller passes the spawn-recorded
    proc_start; the live /proc starttime is re-checked before the first
    signal. On mismatch (pid recycled or already gone) nothing is signaled,
    no marker is written, and one WARNING names the workspace path and both
    start ticks -- never process content. On a passed check the marker is
    written before the first signal so later snapshots read "terminated",
    not "crashed" (defect found in s2, patch spec authored by season s4 w1).
    """
    live = _proc_start_ticks(pid)
    if live != proc_start:
        logger.warning(
            "%s: pid %s identity mismatch (recorded start %s, live %s); not signaled",
            ws, pid, proc_start, live,
        )
        return
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


def _stall_stop_record(
    root: Path, sid: str, snaps: dict[str, dict[str, Any]], ended_at: float,
    stall_s: float,
) -> dict[str, Any]:
    """s60 w1: the auditable stop record for a stopped_stall finalize.

    Names the progress rule and, per agent, which progress events counted
    (each source stamp), the event counters, and the last-progress age at
    the stop. Sources absent from a meta do not appear: an empty sources
    map with a large age is the honest shape of a true stall. Never carries
    stream content -- counts, byte sizes, stamps, ages only.
    """
    agents: dict[str, Any] = {}
    for aname, snap in snaps.items():
        try:
            meta = json.loads(
                (season_dir(root, sid) / aname / "state.json").read_text(
                    encoding="utf-8",
                ),
            )
            sources = {
                key: meta[key]
                for key in ("last_progress", "last_tool_use", "last_ws_progress")
                if isinstance(meta.get(key), (int, float))
            }
            stamps = [float(meta["started_at"]), *sources.values()]
            agents[aname] = {
                "state": snap["state"],
                "sources": sources,
                "tool_use_count": meta.get("tool_use_count"),
                "ws_bytes": meta.get("ws_bytes"),
                "log_size": meta.get("log_size"),
                "last_progress_age_s": round(ended_at - max(stamps), 1),
            }
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return {
        "rule": (
            "progress = agent.log appended-byte growth, or any parsed"
            " tool_use event, or watched workspace write growth; stalled"
            " = now - newest source > stall_s (s60 w1)"
        ),
        "stall_s": stall_s,
        "agents": agents,
    }


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
                _terminate(
                    season_dir(root, sid) / aname, meta["pid"],
                    meta.get("proc_start"),
                )
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
        # M5 (codex-review-2026-09-14): the all-terminal path arrives as
        # "completed"; a failed or crashed agent downgrades the recorded
        # status to "failed" so the season's exit is honest. Rule-stopped
        # seasons (stopped_stall, stopped_operator) keep their rule status;
        # the agents map carries the per-agent truth. "terminated" is an
        # engine stop, not an agent failure (H9: budget-stopped agents leave
        # the season completed).
        if status == "completed" and any(
            snap["state"] in ("failed", "crashed") for snap in final_snaps.values()
        ):
            status = "failed"
        state["agents"] = final_snaps
        state["status"] = status
        state["ended_at"] = time.time()
        if status == "stopped_stall":
            # s60 w1: name the progress rule and the per-agent evidence in
            # the stop record, so a stall stop is auditable after the fact.
            state["stall_stop"] = _stall_stop_record(
                root, sid, final_snaps, state["ended_at"],
                float(state.get("stall_s", 2700.0)),
            )
            record = state["stall_stop"]
            logger.warning(
                "season %s stopped_stall: stall_s=%g; last-progress ages %s",
                sid, record["stall_s"],
                {n: r["last_progress_age_s"] for n, r in record["agents"].items()},
            )
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


def _validate_benih(
    season: dict[str, Any], routes: dict[str, str], root: Path, sid: str,
) -> None:
    """H5 layer 1 (codex-review-2026-09-14): validate every benih before any spawn.

    Route resolution, prompt existence, and lane preparation all raise here,
    before the first Popen, so a bad second benih can never orphan a live
    first child. prepare_lane is idempotent (touch, never truncate), so the
    later _child_env call re-prepares the same lane safely.
    """
    for benih in _writer_table(season):
        name = str(benih["name"])
        if routes.get(str(benih["route"])) is None:
            msg = (
                f"benih '{name}': route '{benih['route']}' not in rumpun.yaml "
                "routes; run 'rumpun models --write' first"
            )
            raise EngineError(msg)
        if not (root / benih["prompt"]).is_file():
            msg = f"benih '{name}': prompt not found: {benih['prompt']}"
            raise EngineError(msg)
        group = benih.get("collab")
        if group:
            collab.prepare_lane(root, sid, str(group))


def start_season(yaml_path: Path, root: Path) -> dict[str, Any]:
    """Spawn (or reattach to) a season and watch it to a terminal state.

    H5 (codex-review-2026-09-14): startup cannot abandon live children. All
    benih validate before the first Popen; any failure inside the spawn loop
    terminates the already-spawned children (identity-checked), records the
    error in state as status "failed", and re-raises. Layer 3: each child's
    spawn intent persists before Popen, so a crash between Popen and the pid
    save leaves the child registered (pid-None intent) and recoverable: a
    reattaching starter adopts a live child from the workspace state.json,
    or clears the stale intent and respawns.
    """
    resolved_yaml = yaml_path.resolve()
    if resolved_yaml.parent.name not in ("seasons", "musim"):
        msg = (
            f"{resolved_yaml} is outside seasons/ canonical placement (legacy"
            " musim/ accepted); only seasons there can start (drafts go through"
            " evolve apply)"
        )
        raise EngineError(msg)
    season = yamlio.load(yaml_path)
    sid = str(season["id"])
    cfg = yamlio.load(root / "rumpun.yaml")
    routes: dict[str, str] = cfg.get("routes") or {}
    if not routes:
        msg = "rumpun.yaml routes is empty; run 'rumpun models --write' first"
        raise EngineError(msg)
    stall_s, budget_s = _stop_rules(season)
    # One lock acquisition spans load, the finished check, validation, the
    # initial save, and the spawn loop's per-benih saves: a second starter
    # for this sid blocks here, then reads the fully spawned state and
    # reattaches.
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
        try:
            # H5 layer 1: every route, prompt, and lane resolves before the
            # first Popen (a missing second route never orphans the first).
            _validate_benih(season, routes, root, sid)
            for benih in _writer_table(season):
                name = str(benih["name"])
                entry = spawned.get(name)
                if entry is not None and entry.get("pid") is not None:
                    continue  # reattach: already spawned, keep watching it
                if entry is not None:
                    # pid-None intent from a crash between Popen and the pid
                    # save: adopt a live child from the workspace state.json,
                    # else drop the stale intent and respawn below.
                    ws_meta_path = season_dir(root, sid) / name / "state.json"
                    adopted = False
                    if ws_meta_path.is_file():
                        ws_meta = json.loads(
                            ws_meta_path.read_text(encoding="utf-8"),
                        )
                        if _alive(ws_meta.get("pid", 0), ws_meta.get("proc_start")):
                            spawned[name] = {
                                "pid": ws_meta["pid"],
                                "proc_start": ws_meta.get("proc_start"),
                            }
                            state["spawned"] = spawned
                            _save_state(root, sid, state, state_lock)
                            adopted = True
                    if adopted:
                        continue
                    del spawned[name]
                template = routes[str(benih["route"])]
                # H3 (codex-review-2026-09-14): resolve before spawning so the
                # wrapper's {prompt}/{exit} paths are absolute and cwd=ws agrees
                # with them; agents run inside their workspace, not the repo dir.
                ws = (season_dir(root, sid) / name).resolve()
                ws.mkdir(parents=True, exist_ok=True)
                prompt_src = root / benih["prompt"]
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
                # H5 layer 3: persist the spawn intent before Popen, so a
                # crash between Popen and the pid save leaves the child
                # registered in state["spawned"] (pid-None intent) and
                # recoverable by a reattaching starter.
                spawned[name] = {"pid": None, "proc_start": None}
                state["spawned"] = spawned
                _save_state(root, sid, state, state_lock)
                with (ws / "agent.log").open("wb") as log_f:
                    proc = subprocess.Popen(
                        ["/bin/sh", "-c", wrapped], stdout=log_f, stderr=log_f,
                        cwd=ws, env=child_env,
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
        except Exception as exc:
            # H5 layer 2: a failing startup must not abandon live children.
            logger.exception("season %s: startup failed; cleaning up", sid)
            for aname, meta in spawned.items():
                pid = meta.get("pid")
                if pid is None or not _alive(pid, meta.get("proc_start")):
                    continue
                _terminate(
                    season_dir(root, sid) / aname, pid, meta.get("proc_start"),
                )
            stale = [k for k, v in spawned.items() if v.get("pid") is None]
            for key in stale:
                del spawned[key]  # intent-only entries: nothing was spawned
            state["spawned"] = spawned
            state["status"] = "failed"
            state["error"] = f"{type(exc).__name__}: {exc}"
            state["ended_at"] = time.time()
            _save_state(root, sid, state, state_lock)
            raise
    budgets = {
        str(b["name"]): float((b.get("budget") or {}).get("minutes", 0))
        for b in _writer_table(season)
    }
    # Content-based stall progress (s24): per live agent, the last-seen
    # agent.log byte size and the time that size last grew. A grown size is
    # durable progress; an unchanged size provides none whatever mtime says.
    # The stat rides the existing cycle -- zero new polling.
    log_hist: dict[str, tuple[int, float]] = {}
    # s31 w1 render-on-change: the digest cache is closure-held (the watcher
    # is single-season scoped). First cycle always renders (cache starts
    # None); a cycle re-renders only on changed state.json bytes. The read
    # rides the existing cycle -- zero new polling.
    last_render_digest: bytes | None = None
    while True:
        state = _load_state(root, sid) or state
        if state.get("status") != "running":
            break  # stop_season finalized it underneath us
        if state_hook is not None:
            try:
                digest = _state_digest(root, sid)
            except OSError:
                logger.exception("state digest read failed (ignored)")
            else:
                if digest != last_render_digest:
                    last_render_digest = digest
                    # Downgraded per s31 w1: the per-render INFO comes from
                    # report functions; the hook itself adds no INFO.
                    logger.debug("state.json changed; rendering")
                    try:
                        state_hook()
                    except Exception:
                        logger.exception("state hook failed (ignored)")
        snaps = _agents_snaps(root, sid, stall_s, log_hist)
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
            # s60 w1: the same cycle watches workspace write growth, so a
            # quiet-stdout writer busy on files keeps resetting the stall
            # clock (one stat walk per live agent per cycle -- zero new
            # polling).
            _scan_agent_writes(ws, meta)
            # H9 (codex-review-2026-09-14): each agent enforces its own
            # budget, not the season max. An agent past ITS deadline is
            # terminated; the additive terminated_budget key records the
            # reason in its state.json and snap, and the season ends
            # completed once every agent is terminal, naturally or
            # budget-stopped.
            minutes = budgets.get(aname, 0.0)
            if minutes > 0 and time.time() - snap["started_at"] > minutes * 60:
                logger.warning(
                    "agent %s is past its %g-minute budget; terminating",
                    aname, minutes,
                )
                _terminate(ws, meta["pid"], meta.get("proc_start"))
                if (ws / "terminated").is_file():
                    meta["terminated_budget"] = True
                    _write_agent_state_guarded(root, sid, ws, meta, None)
                    snap["state"] = "terminated"
                    snap["terminated_budget"] = True
            # Record this cycle's observed log size for the next snap (the
            # content rule compares across cycles); a grown size moves the
            # agent's progress time forward.
            with contextlib.suppress(OSError):
                size = (ws / "agent.log").stat().st_size
                prev_size, prev_at = log_hist.get(aname, (size, 0.0))
                grew = size > prev_size and aname in log_hist
                log_hist[aname] = (size, time.time() if grew else prev_at)
        states = {s["state"] for s in snaps.values()}
        if states and states <= TERMINAL | {"terminated"}:
            return _finalize(root, sid, "completed", snaps)
        if any(s["state"] == "stalled" for s in snaps.values()):
            return _finalize(root, sid, "stopped_stall", snaps)
        if _stop_flag(root, sid).exists():
            return _finalize(root, sid, "stopped_operator", snaps)
        time.sleep(1)
    return read_status(root, sid)


def read_persisted_status(root: Path, sid: str) -> dict[str, Any]:
    """Persisted season state exactly as stored: no /proc reads, no clock (M1).

    Deterministic views (report) render from this: identical state.json
    bytes produce identical pages, RUNNING seasons included. The live
    reader (read_status) recomputes agent snaps from /proc and the clock
    for running seasons and stays the P36 surface-0 machine view for the
    cli and harvest.
    """
    state = _load_state(root, sid)
    if state is None:
        msg = f"no season state for '{sid}'; run 'rumpun season start' first"
        raise EngineError(msg)
    return state


def read_status(root: Path, sid: str) -> dict[str, Any]:
    """Live season snapshot (P36 surface 0). Never mutates state."""
    state = read_persisted_status(root, sid)
    if state["status"] == "running":
        state["agents"] = _agents_snaps(root, sid, float(state.get("stall_s", 2700.0)))
    return state


_EXIT_ZERO_STATUSES = frozenset({"running", "completed", "stopped_operator"})


def status_exit_code(status: str) -> int:
    """M5 (codex-review-2026-09-14): season status -> verb exit code.

    The single-season verbs (season start/stop/status/show) return this
    mapping, so a failed season can never exit 0 again:
    - 0: completed (every agent exited 0), stopped_operator (the operator
      asked for the stop; not an agent failure), running.
    - 1: failed (>=1 agent failed/crashed, or a startup failure),
      stopped_stall (the progress rule fired), stopped_budget (reserved
      status; the report palette already knows it; no current producer),
      and any unknown status -- an unrecognized terminal state must not
      look healthy.
    'season list' stays an informational surface and exits 0.
    """
    return 0 if status in _EXIT_ZERO_STATUSES else 1


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
