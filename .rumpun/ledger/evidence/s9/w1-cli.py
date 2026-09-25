"""rumpun CLI — verb dispatch (layout per ratified P36 D9).

Top-level: init, lint, graph, models, board, harvest, direct.
Groups: season start/stop/status/list/show/report,
evolve plan/approve/apply/reject/rollback.
Implemented (v0.9.0): init, lint, graph, models, board, harvest,
direct [--list], season start/status/stop/list/show/report (report --serve),
evolve plan/apply/approve/reject/rollback.
The stub registry is empty: every P36 D9 verb exists; unknown verbs exit 2.
Build order lives in DESIGN.md section 10.
"""

from __future__ import annotations

import argparse
import functools
import json
import logging
import re
import subprocess
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from rumpun import __version__, akar, collab, engine, scaffold, yamlio
from rumpun import evolve as evolve_mod
from rumpun import graph as graph_mod
from rumpun import harvest as harvest_mod
from rumpun import lint as lint_mod
from rumpun import report as report_mod
from rumpun import routes as routes_mod

logger = logging.getLogger("rumpun")

NOT_IMPLEMENTED: dict[str, str] = {}

SEASON_STUBS: dict[str, str] = {}

BOOKKEEPING: frozenset[str] = frozenset(
    {
        "agent.log",
        "exit",
        "prompt.md",
        "prompt-meta.yaml",
        "state.json",
        "terminated",
        "terminated.tmp",
        "__pycache__",
    }
)


def _setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def _find_config(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / ".rumpun" / "rumpun.yaml").is_file():
            return candidate / ".rumpun" / "rumpun.yaml"
    return None


def _project_root(start: Path) -> Path:
    cfg = _find_config(start)
    if cfg is None:
        msg = "no .rumpun/rumpun.yaml found above cwd; run 'rumpun init' first"
        raise lint_mod.LintError(msg)
    return cfg.parent


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    scaffold.init_project(target)
    logger.info("initialized rumpun project at %s", target)
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    findings = lint_mod.lint(Path(args.file).resolve())
    errors = [f for f in findings if f.severity == "error"]
    for f in findings:
        line = f"{f.path}: {f.message}" if f.path else f.message
        (logger.error if f.severity == "error" else logger.warning)(line)
    if errors:
        warnings = len(findings) - len(errors)
        logger.error("lint FAILED: %d error(s), %d warning(s)", len(errors), warnings)
        return 1
    logger.info("lint OK (%d warning(s))", len(findings) - len(errors))
    return 0


def cmd_graph(args: argparse.Namespace) -> int:
    print(graph_mod.mermaid(Path(args.file).resolve()))
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    """Local agent-route detector (build order step 2). Read-only by
    default; --write fills rumpun.yaml routes; --probe spends quota."""
    for row in routes_mod.detect_clis():
        mark = "yes" if row["present"] == "yes" else "no "
        ver = f" ({row['version']})" if row["version"] else ""
        print(f"  {row['name']:<10} {mark}{ver}")
    print("\nclaude-binary routes (this machine):")
    for route in routes_mod.claude_routes():
        print(f"  [{route['family']:<8}] {route['desc']}")
        print(f"      spawn: {route['command']}")
    print("\ncodex routes (models_cache when present, else default):")
    for route in routes_mod.codex_model_routes():
        print(f"  [{route['family']:<12}] {route['desc']}")
        print(f"      spawn: {route['command']}")
    if getattr(args, "write", False):
        cfg = _find_config(Path.cwd())
        if cfg is None:
            logger.error("--write needs a rumpun project (no rumpun.yaml above cwd)")
            return 1
        count = routes_mod.write_routes(cfg)
        yamlio.load(cfg)  # re-parse: a broken patch must fail loudly here
        logger.info("wrote %d routes into %s", count, cfg)
    if getattr(args, "probe", False):
        print("\n--probe: one tiny completion per claude route (spends quota)...")
        for route in routes_mod.claude_routes():
            cmd = route["command"].replace("<model>", "fable")
            if "{prompt}" in cmd:
                cmd = cmd.replace("{prompt}", "'Reply with exactly: READY'")
            t0 = time.monotonic()
            try:
                out = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True,
                    timeout=90, check=False,
                )
                dt = time.monotonic() - t0
                lines = (out.stdout or "").strip().splitlines()
                reply = lines[-1][:60] if lines else "(empty)"
                ok = "yes" if out.returncode == 0 and reply != "(empty)" else "NO"
                print(f"  {ok} [{route['family']}] {dt:.1f}s — {reply}")
            except subprocess.TimeoutExpired:
                print(f"  NO [{route['family']}] timeout (90s)")
    return 0


def cmd_direct(args: argparse.Namespace) -> int:
    """P8 directives: the human seat's channel. Appends only touch the
    artifact; nothing is injected into a running process, and the jsonl
    records pending versus consumed."""
    root = _project_root(Path.cwd())
    lane = {
        "file": str(root / "akar" / "directives.jsonl"),
        "lock": str(root / "akar" / "directives.lock"),
    }
    if args.list:
        path = Path(lane["file"])
        events = collab.read_events(lane) if path.is_file() else []
        if not events:
            print("no directives")
            return 0
        pending = [e for e in events if e.get("status") == "pending"]
        consumed = [e for e in events if e.get("status") != "pending"]
        for event in pending + consumed:
            print(f"{event['seq']}  {event.get('status')}  {event.get('text')}")
        return 0
    if not args.text:
        logger.error("direct requires TEXT (append) or --list")
        return 2
    event = collab.append_event(
        lane, "operator", {"text": args.text, "status": "pending"}
    )
    print(f"{event['seq']}  {event['status']}  {event['text']}")
    return 0


def _render_state(state: dict) -> str:
    """Human table for a season snapshot (P36 surface 1, snapshot form)."""
    started = time.strftime("%H:%M:%S", time.localtime(state["started_at"]))
    end = state.get("ended_at") or time.time()
    dur = end - state["started_at"]
    lines = [f"season {state['id']}: {state['status']} ({dur:.0f}s, started {started})"]
    agents = state.get("agents") or {}
    for name in sorted(agents):
        a = agents[name]
        code = "" if a.get("exit_code") is None else f" code {a['exit_code']}"
        lines.append(
            f"  {a['name']:<8} {a['route']:<14} {a['state']:<11}"
            f"{code} {a['seconds']}s"
        )
    return "\n".join(lines)


def _lint_preflight(yaml_path: Path) -> bool:
    """P27 boundary: errors block start. Returns True when clean."""
    findings = lint_mod.lint(yaml_path)
    errors = [f for f in findings if f.severity == "error"]
    for f in findings:
        line = f"{f.path}: {f.message}" if f.path else f.message
        (logger.error if f.severity == "error" else logger.warning)(line)
    return not errors


def cmd_season_start(args: argparse.Namespace) -> int:
    yaml_path = Path(args.file).resolve()
    if not _lint_preflight(yaml_path):
        logger.error("lint errors block season start (P27 preflight)")
        return 1
    root = _project_root(yaml_path.parent)
    state = engine.start_season(yaml_path, root)
    if getattr(args, "json", False):
        print(json.dumps(state, indent=2))
    else:
        print(_render_state(state))
    return 0


def cmd_season_status(args: argparse.Namespace) -> int:
    root = _project_root(Path.cwd())
    state = engine.read_status(root, args.id)
    if getattr(args, "json", False):
        print(json.dumps(state, indent=2))
    else:
        print(_render_state(state))
    return 0


def _deliverables(ws: Path) -> list[str]:
    """Relative names of files in an agent workspace, minus engine bookkeeping."""
    if not ws.is_dir():
        return []
    out: list[str] = []
    for path in sorted(ws.rglob("*")):
        rel = path.relative_to(ws)
        if path.is_file() and not (BOOKKEEPING & set(rel.parts)):
            out.append(rel.as_posix())
    return out


def _lanes(sdir: Path) -> dict[str, int]:
    """Non-blank event count per lane-*.jsonl in the season _season dir."""
    counts: dict[str, int] = {}
    for path in sorted(sdir.glob("lane-*.jsonl")):
        with path.open(encoding="utf-8") as fh:
            counts[path.name] = sum(1 for line in fh if line.strip())
    return counts


def cmd_season_show(args: argparse.Namespace) -> int:
    root = _project_root(Path.cwd())
    state = engine.read_status(root, args.id)  # unknown id -> EngineError
    sdir = engine.season_dir(root, args.id)
    agents = state.get("agents") or {}
    deliverables = {name: _deliverables(sdir / name) for name in sorted(agents)}
    lanes = _lanes(sdir / "_season")
    if getattr(args, "json", False):
        payload = {
            "id": state["id"],
            "status": state["status"],
            "started_at": state["started_at"],
            "ended_at": state.get("ended_at"),
            "agents": agents,
            "deliverables": deliverables,
            "lanes": lanes,
        }
        print(json.dumps(payload, indent=2))
        return 0
    print(_render_state(state).splitlines()[0])
    for name, files in deliverables.items():
        listed = ", ".join(files) if files else "(no deliverables)"
        print(f"  {name}: {listed}")
    for lane, count in lanes.items():
        print(f"  {lane}  {count} events")
    return 0


def _season_sort_key(path: Path) -> tuple[int, str]:
    m = re.fullmatch(r"s(\d+)", path.stem)
    return (int(m.group(1)) if m else 0, path.stem)


def cmd_season_list(_args: argparse.Namespace) -> int:
    """One line per season, sorted by number (absorbs old 'runs', P36 D9)."""
    root = _project_root(Path.cwd())
    for path in sorted((root / "musim").glob("s*.yaml"), key=_season_sort_key):
        sid = yamlio.load(path).get("id") or path.stem
        try:
            state = engine.read_status(root, sid)
        except engine.EngineError:
            print(f"{sid}  no state")
            continue
        end = state.get("ended_at") or time.time()
        agents = state.get("agents") or {}
        dur = end - state["started_at"]
        print(f"{sid}  {state['status']}  {dur:.0f}s  {len(agents)} agents")
    return 0


def cmd_season_stop(args: argparse.Namespace) -> int:
    root = _project_root(Path.cwd())
    state = engine.stop_season(root, args.id)
    print(_render_state(state))
    return 0


def _serve_rimba(rimba: Path, sid: str) -> int:
    """Serve the rimba tree on 127.0.0.1:8611 until Ctrl-C; exit 0."""
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(rimba))
    try:
        with ThreadingHTTPServer(("127.0.0.1", 8611), handler) as httpd:
            logger.info("serving %s at http://127.0.0.1:8611 (^C to stop)", rimba)
            print(f"http://localhost:8611/{sid}/report.html")
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("serve stopped")
    return 0


def cmd_season_report(args: argparse.Namespace) -> int:
    root = _project_root(Path.cwd())
    target = report_mod.render_report(root, args.id)
    if getattr(args, "serve", False):
        return _serve_rimba(root / "rimba", args.id)
    print(target)
    return 0


def cmd_harvest(args: argparse.Namespace) -> int:
    root = _project_root(Path.cwd())
    path = harvest_mod.harvest_season(root, args.id, args.verdict, args.implies)
    logger.info("season %s harvested -> %s", args.id, path)
    return 0


def cmd_evolve_plan(args: argparse.Namespace) -> int:
    yaml_path = Path(args.file).resolve()
    root = _project_root(yaml_path.parent)
    drafted = evolve_mod.draft_next(root, yaml_path)
    logger.info(
        "drafted %s; fill primary_change and evidence, then 'rumpun evolve apply %s'",
        drafted, drafted,
    )
    return 0


def cmd_evolve_apply(args: argparse.Namespace) -> int:
    yaml_path = Path(args.file).resolve()
    root = _project_root(yaml_path.parent)
    evolve_mod.apply(root, yaml_path)
    logger.info("applied: %s is lint-clean", yaml_path)
    return 0


def cmd_evolve_approve(args: argparse.Namespace) -> int:
    """P33 manual stage: the operator's approval becomes an akar record
    (goal line + evidence citation); the draft file itself never changes."""
    yaml_path = Path(args.file).resolve()
    root = _project_root(yaml_path.parent)
    record = evolve_mod.approve_draft(root, yaml_path)
    logger.info("approved %s; akar record %s", yaml_path, record)
    return 0


def cmd_evolve_reject(args: argparse.Namespace) -> int:
    """P33 on_reject: the draft moves to musim/rejected/ and the containment
    policy (rollback_to_last_good, pause, escalate after 2 consecutive
    rejects) is recorded in akar."""
    yaml_path = Path(args.file).resolve()
    root = _project_root(yaml_path.parent)
    record = evolve_mod.reject_draft(root, yaml_path)
    logger.info("rejected %s; draft moved to musim/rejected/; akar record %s",
                yaml_path, record)
    return 0


def cmd_evolve_rollback(args: argparse.Namespace) -> int:
    """P33 containment for an applied season: musim/<sid>.yaml moves to
    musim/rejected/ and the on_reject policy records in akar; code-level
    restore stays an explicit git revert by the operator (the verb never
    runs git)."""
    root = _project_root(Path.cwd())
    record = evolve_mod.rollback_season(root, args.id)
    logger.info("rolled back %s; season moved to musim/rejected/; akar record %s",
                args.id, record)
    return 0


def _not_implemented(name: str, what: str):
    def _run(_args: argparse.Namespace) -> int:
        logger.error("'%s' is not implemented yet: %s", name, what)
        return 2

    return _run


def _add_stub(sub: argparse.ArgumentParser, name: str, what: str) -> None:
    p = sub.add_parser(name, help=what)
    p.set_defaults(func=_not_implemented(name, what))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rumpun", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="scaffold a rumpun project in TARGET")
    p_init.add_argument("target", nargs="?", default=".")
    p_init.set_defaults(func=cmd_init)

    for verb, func, help_text in [
        ("lint", cmd_lint, "validate a season YAML (structure, DAG, contracts, citations)"),
        ("graph", cmd_graph, "render a season pipeline as mermaid"),
        ("models", cmd_models, "detect spawnable model routes on this machine"),
    ]:
        p = sub.add_parser(verb, help=help_text)
        if verb == "models":
            p.add_argument("--write", action="store_true",
                           help="fill rumpun.yaml routes: {} with the detected table")
            p.add_argument("--probe", action="store_true",
                           help="send one tiny completion per claude route (spends quota)")
        else:
            p.add_argument("file", help="season YAML path")
        p.set_defaults(func=func)

    p_direct = sub.add_parser(
        "direct", help="append or list operator directives (P8)",
    )
    p_direct.add_argument(
        "text", nargs="?", help="directive text; recorded with status pending",
    )
    p_direct.add_argument(
        "--list", action="store_true", help="print all directives, pending first",
    )
    p_direct.set_defaults(func=cmd_direct)

    p_board = sub.add_parser("board", help="live season board (P36: snapshot form)")
    p_board.add_argument("id", help="season id, e.g. s1")
    p_board.set_defaults(func=cmd_season_status)

    p_harvest = sub.add_parser("harvest", help="tuai: close a season into akar (step 4)")
    p_harvest.add_argument("id", help="season id, e.g. s2")
    p_harvest.add_argument("--verdict", required=True,
                           choices=["WIN", "LOSS", "NEUTRAL", "INVALID"])
    p_harvest.add_argument("--implies", required=True)
    p_harvest.set_defaults(func=cmd_harvest)

    for verb, what in NOT_IMPLEMENTED.items():
        _add_stub(sub, verb, what)

    p_season = sub.add_parser("season", help="season lifecycle commands")
    season_sub = p_season.add_subparsers(dest="season_command", required=True)
    p_start = season_sub.add_parser("start", help="spawn the season (build order step 3)")
    p_start.add_argument("file", help="season YAML path")
    p_start.add_argument("--json", action="store_true", help="machine-readable output")
    p_start.set_defaults(func=cmd_season_start)
    p_status = season_sub.add_parser("status", help="season snapshot with --json (P36 priority 0)")
    p_status.add_argument("id", help="season id, e.g. s1")
    p_status.add_argument("--json", action="store_true", help="machine-readable output")
    p_status.set_defaults(func=cmd_season_status)
    p_list = season_sub.add_parser("list", help="one line per season: id, status, duration, agents")
    p_list.set_defaults(func=cmd_season_list)
    p_stop = season_sub.add_parser("stop", help="stop the season (build order step 3)")
    p_stop.add_argument("id", help="season id, e.g. s1")
    p_stop.set_defaults(func=cmd_season_stop)
    p_report = season_sub.add_parser("report", help="static HTML season report (P36 surface 2)")
    p_report.add_argument("id", help="season id, e.g. s2")
    p_report.add_argument(
        "--serve", action="store_true",
        help="after rendering, serve rimba/ over HTTP at http://localhost:8611",
    )
    p_report.set_defaults(func=cmd_season_report)
    p_show = season_sub.add_parser(
        "show", help="season detail: status line, deliverables, lanes",
    )
    p_show.add_argument("id", help="season id, e.g. s1")
    p_show.add_argument("--json", action="store_true", help="machine-readable output")
    p_show.set_defaults(func=cmd_season_show)
    if SEASON_STUBS:
        for verb, what in SEASON_STUBS.items():
            _add_stub(season_sub, verb, what)

    p_evolve = sub.add_parser("evolve", help="evolution commands (evolusi)")
    evolve_sub = p_evolve.add_subparsers(dest="evolve_command", required=True)
    p_plan = evolve_sub.add_parser("plan", help="draft the next season YAML (build order step 5)")
    p_plan.add_argument("file", help="parent season YAML path")
    p_plan.set_defaults(func=cmd_evolve_plan)
    p_apply = evolve_sub.add_parser("apply", help="lint-gate a drafted season")
    p_apply.add_argument("file", help="drafted season YAML path")
    p_apply.set_defaults(func=cmd_evolve_apply)
    p_approve = evolve_sub.add_parser(
        "approve", help="approve a drafted evolution; appends the akar approval record",
    )
    p_approve.add_argument("file", help="drafted season YAML path")
    p_approve.set_defaults(func=cmd_evolve_approve)
    p_reject = evolve_sub.add_parser(
        "reject", help="reject a drafted evolution; triggers the on_reject policy (P33)",
    )
    p_reject.add_argument("file", help="drafted season YAML path")
    p_reject.set_defaults(func=cmd_evolve_reject)
    p_rollback = evolve_sub.add_parser(
        "rollback",
        help="contain an applied season; on_reject policy records in akar (P33)",
    )
    p_rollback.add_argument("id", help="applied season id, e.g. s3")
    p_rollback.set_defaults(func=cmd_evolve_rollback)

    return parser


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (lint_mod.LintError, scaffold.ScaffoldError, yamlio.YamlError,
            routes_mod.RoutesError, engine.EngineError, collab.LaneError,
            evolve_mod.EvolveError, akar.AkarError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
