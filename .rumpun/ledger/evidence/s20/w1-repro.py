"""H5/H9 reproductions (s20 w1): startup cleanup + per-agent budgets.

Usage: python repro_h5_h9.py <src-dir>

Runs the three review repros against the given source tree and records one
PASS/FAIL line per assertion. On the unpatched tree the targeted FAILs are
the expected RED evidence; on the patched tree every line must be PASS.
Cleanup runs in finally blocks: no orphan processes or tmp dirs survive.
"""

from __future__ import annotations

import json
import logging
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from rumpun import engine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("repro")

PROMPT = "repro prompt text\n"

RUMPUN_YAML = """\
autonomy:
  stage: manual
  invariants: [goal_immutable]
routes:
  glm: "sleep 30 && cat {prompt} > /dev/null"
  long: "sleep 6 && cat {prompt} > /dev/null"
"""

SEASON_TMPL = """\
id: {sid}
goal: "repro"
metric: "m"
mode: fight
methodology:
  approach: "x"
  evidence: []
  primary_change:
    type: add
    node: execute
    baseline: "b"
    expected_band: "WIN if x"
    eval_window: "r"
    rollback: "git revert"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/w1.md
      writes: results.jsonl
benih:
{benih_block}
stop:
  "on": []
"""

BENIH_TMPL = """\
  - name: {name}
    route: {route}
    prompt: prompts/{name}.md
    knowledge: none
    budget: {{minutes: {minutes}}}
"""


def _project(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "rumpun.yaml").write_text(RUMPUN_YAML, encoding="utf-8")
    (root / "prompts").mkdir(exist_ok=True)
    for name in ("w1", "w2"):
        (root / "prompts" / f"{name}.md").write_text(PROMPT, encoding="utf-8")


def _season_yaml(root: Path, sid: str, benih: list[dict]) -> Path:
    benih_block = "".join(
        BENIH_TMPL.format(name=b["name"], route=b["route"], minutes=b["minutes"])
        for b in benih
    )
    (root / "musim").mkdir(parents=True, exist_ok=True)
    path = root / "musim" / f"{sid}.yaml"
    path.write_text(
        SEASON_TMPL.format(sid=sid, benih_block=benih_block), encoding="utf-8",
    )
    return path


def _ws_meta(root: Path, sid: str, name: str) -> dict:
    path = root / "rimba" / sid / name / "state.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _kill_all(root: Path, sid: str) -> None:
    """Best-effort orphan cleanup: terminate every workspace child."""
    sdir = root / "rimba" / sid
    if not sdir.is_dir():
        return
    for ws in sorted(sdir.iterdir()):
        if not ws.is_dir() or ws.name == "_season":
            continue
        meta_path = ws / "state.json"
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        engine._terminate(ws, meta.get("pid", 0), meta.get("proc_start"))


def _state(root: Path, sid: str) -> dict:
    return json.loads(
        (root / "rimba" / sid / "_season" / "state.json").read_text(encoding="utf-8"),
    )


def _alive(engine_ref, pid: int, start: int | None) -> bool:
    return engine_ref._alive(pid, start)


_results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str) -> None:
    _results.append((name, ok, detail))
    logger.info("%s %s -- %s", "PASS" if ok else "FAIL", name, detail)


def repro1(root: Path) -> None:
    """Missing second route: no child may survive the failed startup."""
    sid = "h5r1"
    yaml_path = _season_yaml(root, sid, [
        {"name": "w1", "route": "glm", "minutes": 30},
        {"name": "w2", "route": "missing", "minutes": 30},
    ])
    try:
        engine.start_season(yaml_path, root)
        record("r1:raises", False, "start_season returned instead of raising")
        return
    except engine.EngineError as exc:
        record("r1:raises", True, f"EngineError: {exc}")
    state = _state(root, sid)
    record("r1:status_failed", state.get("status") == "failed", f"status={state.get('status')}")
    record("r1:error_recorded", bool(state.get("error")), f"error={state.get('error', '')!r}")
    record("r1:no_spawned", state.get("spawned") == {}, f"spawned={state.get('spawned')}")
    live = []
    sdir = root / "rimba" / sid
    for ws in sorted(sdir.iterdir()):
        if ws.is_dir() and ws.name != "_season" and (ws / "state.json").is_file():
            meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
            if engine._alive(meta.get("pid", 0), meta.get("proc_start")):
                live.append(ws.name)
    record("r1:no_live_children", not live, f"live={live}")


def repro2(root: Path) -> None:
    """Crash between Popen and the pid save: child must be registered+killable."""
    sid = "h5r2"
    yaml_path = _season_yaml(root, sid, [
        {"name": "w1", "route": "glm", "minutes": 30},
    ])
    orig_save = engine._save_state
    crashed = False

    def crashing_save(root_, sid_, state_, lock_file=None):
        nonlocal crashed
        pids = [v.get("pid") for v in (state_.get("spawned") or {}).values()]
        if not crashed and any(pids):
            crashed = True
            raise RuntimeError("simulated crash between spawn and save")
        return orig_save(root_, sid_, state_, lock_file)

    engine._save_state = crashing_save
    raised = None
    try:
        try:
            engine.start_season(yaml_path, root)
            record("r2:raises", False, "start_season returned instead of raising")
            return
        except RuntimeError as exc:  # the simulated crash re-raised
            raised = exc
        finally:
            engine._save_state = orig_save
        record("r2:raises", raised is not None, f"raised={raised!r}")
        state = _state(root, sid)
        entry = state.get("spawned", {}).get("w1")
        record(
            "r2:registered",
            bool(entry) and entry.get("pid") is not None,
            f"spawned_entry={entry}",
        )
        meta = _ws_meta(root, sid, "w1")
        alive = engine._alive(meta.get("pid", 0), meta.get("proc_start"))
        record(
            "r2:child_killed",
            (not alive) and (root / "rimba" / sid / "w1" / "terminated").is_file(),
            f"alive={alive} terminated_marker={ ... }",
            )
        record(
            "r2:status_failed",
            state.get("status") == "failed" and bool(state.get("error")),
            f"status={state.get('status')} error={state.get('error', '')!r}",
        )
    finally:
        _kill_all(root, sid)


def repro3(root: Path) -> None:
    """Own-budget enforcement: short agent stopped at ITS deadline, long completes."""
    sid = "h5r3"
    yaml_path = _season_yaml(root, sid, [
        {"name": "w1", "route": "glm", "minutes": 0.02},  # 1.2 s stub
        {"name": "w2", "route": "long", "minutes": 30},
    ])
    outcome: dict = {}

    def run() -> None:
        try:
            outcome["season"] = engine.start_season(yaml_path, root)
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    watcher = threading.Thread(target=run, daemon=True)
    watcher.start()
    deadline = time.time() + 30
    while time.time() < deadline and not watcher.is_alive() is False:
        pass  # placeholder replaced below
    # Poll read_status until the season reaches a terminal status or timeout.
    deadline = time.time() + 30
    status = None
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            status = engine.read_status(root, sid)
        except engine.EngineError:
            continue
        if status.get("status") != "running":
            break
    watcher.join(timeout=5)
    final = outcome.get("season") or engine.read_status(root, sid)
    agents = final.get("agents") or {}
    w1 = agents.get("w1") or {}
    w2 = agents.get("w2") or {}
    record("r3:season_completed", final.get("status") == "completed", f"status={final.get('status')}")
    record(
        "r3:short_terminated_budget",
        w1.get("state") == "terminated" and w1.get("terminated_budget") is True,
        f"w1={w1}",
        )
    record(
        "r3:long_completed",
        w2.get("state") == "exited" and w2.get("exit_code") == 0,
        f"w2={w2}",
    )
    record(
        "r3:short_stopped_at_own_deadline",
        bool(w1.get("seconds") is not None and w1["seconds"] < 10),
        f"w1_seconds={w1.get('seconds')} (own deadline 1.2 s + loop)",
    )


def main() -> int:
    logger.info("engine under test: %s", engine.__file__)
    roots = {name: Path(tempfile.mkdtemp(prefix=f"rumpun-{name}-")) for name in ("r1", "r2", "r3")}
    try:
        for name, root in roots.items():
            _project(root)
        repro1(roots["r1"])
        repro2(roots["r2"])
        repro3(roots["r3"])
    finally:
        for name, root in roots.items():
            sid = {"r1": "h5r1", "r2": "h5r2", "r3": "h5r3"}
            _kill_all(root, sid[name])
            shutil.rmtree(root, ignore_errors=True)
        logger.info("verdicts: %s", ", ".join(
            f"{n}={'PASS' if ok else 'FAIL'}" for n, ok, _ in _results
        ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
