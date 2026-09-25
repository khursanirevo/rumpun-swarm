"""rumpun CLI — verb dispatch (layout per ratified P36 D9).

Top-level: init, lint, graph, models, board, harvest, direct, audit.
Groups: season start/stop/status/list/show/report,
evolve plan/approve/apply/reject/rollback.
plugin install/list (s46: pack install into the campaign, list, init --plugin scaffold use).
plugin publish/pull (s53 hub v1: lint-gated push, digest-verified pull over git).
Implemented (v0.11.0): init, lint, graph, models, board, harvest,
direct [--list], audit [--last] [--corpus], season start/status/stop/list/show/report
(report --serve), evolve plan/apply/approve/reject/rollback. harvest
carries optional --band/--observed (s24): the season verdict row keeps the
declared band and observed result again instead of empty strings.
The stub registry is empty: every P36 D9 verb exists; unknown verbs exit 2.
audit is the phase-2 reflection verb (DESIGN section 15): it reads the
season ledger and appends evidence-cited candidate mutations.
check is the independent artifact check verb (s56): it runs the s55
checker (tools/artifact_check.py) as an isolated subprocess and passes
the verdict exit through; the record lands in the default ledger dir
unless --out-dir redirects.
harvest (s57) runs that same checker subprocess once the close's own
writes are done: sid plus the repo HEAD, the check-<sid> record landing
beside the harvest record in the default ledger dir. The honesty
protocol (s57): a check DELTA or structural refusal never suppresses or
rewrites the verdict row or the harvest record; the harvest logs the
check outcome, and the close's exit reflects the harvest alone unless
--strict passes the check exit through (0 VERIFIED / 1 DELTA / 2
structural refusal).
waive (s65) is the explicit operator release for the engine's season-start
containment gate: while the previous close's check-<sid> record stands
DELTA or refused, season start refuses until a later VERIFIED check record
or the sha-sealed waiver-<sid> ledger record (this verb appends it through
the ledger discipline) lands.
epics (s58) renders the epic rollup from .rumpun/epics.yaml: one line per
epic (id, season span, X WIN / Y LOSS / Z other, title); --init scaffolds
the declaration from the season yamls; a missing file is a flat hint, not
an error (directive seq 5: epics as data, ledger append-only).
kanban (s66, directive seq 7) renders the campaign board from existing
state -- BACKLOG (armed audit candidates, drafted-only seeds), DOING
(running seasons), NEED HUMAN (unset campaign_cost_cap, containment
blocks, pending directives; the seq 8 four-sentence card format), DONE
(harvested seasons with verdict + salvage marks). No new state file.

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

from rumpun import __version__, akar, collab, engine, paths, scaffold, yamlio
from rumpun import audit as audit_mod
from rumpun import epics as epics_mod
from rumpun import evolve as evolve_mod
from rumpun import graph as graph_mod
from rumpun import harvest as harvest_mod
from rumpun import lint as lint_mod
from rumpun import plugin as plugin_mod
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


# s56 check verb: hard cap for the checker subprocess (pins alone cap at 240s).
CHECK_TIMEOUT_S = 600


def _setup_logging() -> None:
    """Configure root logging to stderr. force=True replaces any handlers
    already present: without it, basicConfig is a silent no-op when a host
    (pytest caplog) has attached root handlers, and refusals then never
    reach stderr.
    """
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(message)s", force=True
    )



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
    plugins = getattr(args, "plugin", None) or []
    # s47 w1: --plugin names a pack directory; plugin.init_project installs
    # each pack, scaffolds pack-first, seeds the season so lint passes. No
    # --plugin: scaffold.init_project verbatim, one code path.
    plugin_mod.init_project(target, plugins)
    logger.info("initialized rumpun project at %s", target)
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    target = Path(args.file).resolve()
    # s58: the epics declaration has its own gate; `rumpun lint .../epics.yaml`
    # runs lint_epics (id shape, member existence, double membership) instead
    # of the season gate.
    if target.name == epics_mod.EPICS_FILENAME:
        findings = lint_mod.lint_epics(target)
    else:
        findings = lint_mod.lint(target)
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
    ledger = paths.ledger_dir(root)
    lane = {
        "file": str(ledger / "directives.jsonl"),
        "lock": str(ledger / "directives.lock"),
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


def _season_exit(state: dict) -> int:
    """M5 honest exits (codex-review-2026-09-14): the single-season verbs
    start/stop/status/show return the engine's status-to-exit mapping
    (engine.status_exit_code): completed, stopped_operator, and running
    exit 0; failed, stopped_stall, and stopped_budget exit 1. 'season
    list' stays informational and exits 0."""
    return engine.status_exit_code(state.get("status", ""))


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
    sid = yamlio.load(yaml_path).get("id", "?")
    engine.state_hook = lambda: (
        report_mod.render_report(root, sid),
        report_mod.render_index(root),
    )
    try:
        state = engine.start_season(yaml_path, root)
    finally:
        engine.state_hook = None
        try:
            report_mod.render_report(root, sid)
            report_mod.render_index(root)
        except Exception:
            logger.exception("post-season render failed")
    if getattr(args, "json", False):
        print(json.dumps(state, indent=2))
    else:
        print(_render_state(state))
    return _season_exit(state)


def cmd_season_status(args: argparse.Namespace) -> int:
    root = _project_root(Path.cwd())
    state = engine.read_status(root, args.id)
    if getattr(args, "json", False):
        print(json.dumps(state, indent=2))
    else:
        print(_render_state(state))
    return _season_exit(state)


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
        return _season_exit(state)
    print(_render_state(state).splitlines()[0])
    for name, files in deliverables.items():
        listed = ", ".join(files) if files else "(no deliverables)"
        print(f"  {name}: {listed}")
    for lane, count in lanes.items():
        print(f"  {lane}  {count} events")
    return _season_exit(state)


def _season_sort_key(path: Path) -> tuple[int, str]:
    m = re.fullmatch(r"s(\d+)", path.stem)
    return (int(m.group(1)) if m else 0, path.stem)


def cmd_season_list(_args: argparse.Namespace) -> int:
    """One line per season, sorted by number (absorbs old 'runs', P36 D9)."""
    root = _project_root(Path.cwd())
    for path in sorted(paths.seasons_dir(root).glob("s*.yaml"), key=_season_sort_key):
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
    return _season_exit(state)


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
    """s57: the close runs the artifact check. After harvest_season has
    appended the akar record AND written the verdicts.jsonl verdict row,
    the same checker subprocess as cmd_check runs once with the season id
    and the repo HEAD; the check-<sid> record lands in the default ledger
    dir beside the harvest record. Honesty protocol: a check DELTA or
    structural refusal never suppresses or rewrites the verdict row or the
    harvest record -- the outcome is logged (and recorded when the checker
    produced a record), and the exit reflects the harvest alone (0) unless
    --strict passes the check exit through (0 VERIFIED / 1 DELTA / 2
    structural refusal)."""
    root = _project_root(Path.cwd())
    path = harvest_mod.harvest_season(
        root, args.id, args.verdict, args.implies,
        band=args.band, observed=args.observed,
    )
    logger.info("season %s harvested -> %s", args.id, path)
    check_exit = _run_check(root, args.id, "HEAD")
    if check_exit != 0:
        logger.warning(
            "check %s at close: exit %d (recorded; the verdict row stands)",
            args.id, check_exit,
        )
    return check_exit if getattr(args, "strict", False) else 0


def cmd_waive(args: argparse.Namespace) -> int:
    """s65: the explicit operator release for a containment-blocked season
    start. Appends the sha-sealed waiver-<sid> ledger record through the
    akar discipline (append-only, duplicate-refusing); the start gate
    accepts the id waiver-<sid> or the waiver:<sid> alias. --reason is
    recorded verbatim in the body. A warning fires when no blocking check
    record currently stands for sid; the append itself is never refused."""
    root = _project_root(Path.cwd())
    if engine.check_block(root, args.sid) is None:
        logger.warning(
            "no blocking check record for %s; appending the waiver anyway",
            args.sid,
        )
    body = f"season: {args.sid}\nreason: {args.reason}\n"
    record = akar.append_record(
        root,
        f"waiver-{args.sid}",
        f"operator waiver: {args.sid} start block released",
        body,
    )
    logger.info("waiver record -> %s", record)
    return 0


def cmd_kanban(args: argparse.Namespace) -> int:
    """s66 w1 (directive seq 7): the campaign board. The module imports
    lazily: kanban.py lands with the s66 merge, and until then the verb
    reports that and exits 2 instead of breaking the CLI import surface."""
    root = _project_root(Path.cwd())
    try:
        from rumpun import kanban as kanban_mod
    except ImportError:
        logger.error("kanban module is not in this tree yet (lands with the s66 merge)")
        return 2
    print(kanban_mod.render(root))
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    """Phase-2 reflection (DESIGN section 15): read the season ledger,
    append the evidence-cited candidate-mutation akar record, and print the
    candidates; nothing else is mutated. With --corpus (s30 w1) a fresh
    corpus run precedes ingestion: refresh_corpus_matrix runs the repo's
    tools/replay_corpus.py as an isolated subprocess and run_audit ingests
    the matrix that run just wrote; a runner error is an AuditError, never
    a silent stale-matrix fallback."""
    root = _project_root(Path.cwd())
    corpus_matrix = None
    if getattr(args, "corpus", False):
        corpus_matrix = audit_mod.refresh_corpus_matrix(root, audit_mod.CORPUS_RUNNER)
        logger.info("fresh corpus matrix -> %s", corpus_matrix)
    record = audit_mod.run_audit(root, last_n=args.last, corpus_matrix=corpus_matrix)
    logger.info("reflection audit -> %s", record)
    for line in audit_mod.candidate_lines(record):
        print(line)
    return 0


def cmd_epics(args: argparse.Namespace) -> int:
    """s58 (directive seq 5): the epic rollup verb. Reads .rumpun/epics.yaml
    (a missing file is a flat hint, exit 0 -- no epics is not an error),
    lints it (findings logged; errors exit 1 after the render), and prints
    one line per epic: id, the member seasons' span, the X WIN / Y LOSS /
    Z other verdict rollup, and the title; a member with no run state is
    marked on the line, never counted. The ledger is never written. --init
    scaffolds the declaration from the season yamls and refuses to
    overwrite an existing one.
    """
    root = _project_root(Path.cwd())
    target = epics_mod.epics_path(root)
    if getattr(args, "init", False):
        try:
            epics_mod.init(root)
        except epics_mod.EpicsError as exc:
            logger.error("%s", exc)
            return 1
        logger.info(
            "next: split the campaign epic as needed, then run 'rumpun epics'"
        )
        return 0
    if not target.is_file():
        print(
            f"no {target}; seasons are not grouped into epics yet"
            " -- run 'rumpun epics --init'"
        )
        return 0
    findings = lint_mod.lint_epics(target)
    for finding in findings:
        text = f"{finding.path}: {finding.message}" if finding.path else finding.message
        (logger.error if finding.severity == "error" else logger.warning)(text)
    for row in epics_mod.render(root):
        print(row)
    errors = [f for f in findings if f.severity == "error"]
    if errors:
        logger.error("epics lint FAILED: %d error(s)", len(errors))
        return 1
    return 0


def _run_check(
    root: Path, sid: str, close_commit: str, out_dir: Path | None = None,
) -> int:
    """The cmd_check path as one callable: the s55 checker subprocess.

    Same contract as the check verb: isolated subprocess under the repo
    venv's python when present, else the current interpreter; the
    checker's stderr account is re-logged; returns 0 VERIFIED, 1 DELTA,
    2 structural refusal (and 2 also for a missing checker, a timeout, or
    a spawn error). The record lands in the checker's default ledger dir
    unless out_dir redirects. Callers own the honesty policy over the
    returned exit.
    """
    repo = root.parent
    runner = repo / "tools" / "artifact_check.py"
    if not runner.is_file():
        logger.error("checker not found: %s (repo %s)", runner, repo)
        return 2
    venv_python = repo / ".venv" / "bin" / "python"
    python = str(venv_python) if venv_python.is_file() else sys.executable
    argv = [python, str(runner), sid, close_commit]
    if out_dir is not None:
        argv += ["--out-dir", str(out_dir)]
    logger.info("check %s @ %s -> %s", sid, close_commit[:12], runner)
    try:
        proc = subprocess.run(
            argv, cwd=str(repo), capture_output=True, text=True,
            timeout=CHECK_TIMEOUT_S, check=False,
        )
    except subprocess.TimeoutExpired:
        logger.error("checker exceeded %ds: %s", CHECK_TIMEOUT_S, runner)
        return 2
    except OSError as exc:
        logger.error("checker could not start: %s: %s", runner, exc)
        return 2
    for line in (proc.stderr or "").splitlines():
        if line.strip():
            logger.info("%s", line)
    if proc.returncode != 0:
        logger.error(
            "check %s @ %s: checker exit %d",
            sid, close_commit[:12], proc.returncode,
        )
    else:
        logger.info("check %s: exit 0", sid)
    return proc.returncode


def cmd_check(args: argparse.Namespace) -> int:
    """s56: the s55 checker (tools/artifact_check.py) as a verb. Runs as an
    isolated subprocess under the repo venv's python when present, else the
    current interpreter (the audit refresh_corpus_matrix convention); the
    checker's stderr account is re-logged here and the verdict exit passes
    through: 0 VERIFIED, 1 DELTA, 2 structural refusal. The record lands in
    the default ledger dir unless --out-dir redirects. s57: the body moved
    to _run_check so the harvest close can ride the same path; the verb is
    that helper verbatim."""
    root = _project_root(Path.cwd())
    return _run_check(root, args.sid, args.close_commit, out_dir=args.out_dir)


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
    """P33 manual stage: the operator's approval becomes a ledger record
    (goal line + evidence citation); the draft file itself never changes."""
    yaml_path = Path(args.file).resolve()
    root = _project_root(yaml_path.parent)
    record = evolve_mod.approve_draft(root, yaml_path)
    logger.info("approved %s; ledger record %s", yaml_path, record)
    return 0


def cmd_evolve_reject(args: argparse.Namespace) -> int:
    """P33 on_reject: the draft moves to .rumpun/seasons/rejected/ and the containment
    policy (rollback_to_last_good, pause, escalate after 2 consecutive
    rejects) is recorded as a ledger record."""
    yaml_path = Path(args.file).resolve()
    root = _project_root(yaml_path.parent)
    record = evolve_mod.reject_draft(root, yaml_path)
    logger.info("rejected %s; draft moved to .rumpun/seasons/rejected/; ledger record %s",
                yaml_path, record)
    return 0


def cmd_evolve_rollback(args: argparse.Namespace) -> int:
    """P33 containment for an applied season: .rumpun/seasons/<sid>.yaml moves to
    .rumpun/seasons/rejected/ and the on_reject policy is recorded as a ledger record; code-level
    restore stays an explicit git revert by the operator (the verb never
    runs git)."""
    root = _project_root(Path.cwd())
    record = evolve_mod.rollback_season(root, args.id)
    logger.info("rolled back %s; season moved to .rumpun/seasons/rejected/; ledger record %s",
                args.id, record)
    return 0


def cmd_plugin_install(args: argparse.Namespace) -> int:
    """s46: digest-verified, lint-gated install of PACKDIR into the campaign
    rooted at cwd. No .rumpun is needed yet, so install can precede init,
    which the init --plugin flow requires."""
    record = plugin_mod.plugin_install(Path.cwd(), Path(args.packdir).resolve())
    logger.info("install record: %s", record)
    return 0


def cmd_plugin_list(_args: argparse.Namespace) -> int:
    """s46: one line per installed pack: name, version, digest."""
    for record in plugin_mod.plugin_list(Path.cwd()):
        print(f"{record['name']}  {record['version']}  {record['digest']}")
    return 0


def cmd_plugin_distill(args: argparse.Namespace) -> int:
    """s50: draft a pack of generalized priors from the campaign's proven
    gates at <cwd>/.rumpun/plugins/<name>-draft/, for review. plugin install
    is the promotion path and re-gates everything (digest verify, lint gate,
    priors-only copy)."""
    result = plugin_mod.plugin_distill(Path.cwd(), args.pack_name, args.source)
    logger.info("distill result: %s", result)
    return 0


def cmd_plugin_publish(args: argparse.Namespace) -> int:
    """s53 hub v1: lint-gate and digest-verify the installed pack NAME, then
    push it to REMOTE as a git repo (pack = repo, publish = push)."""
    result = plugin_mod.plugin_publish(Path.cwd(), args.name, args.remote)
    logger.info("publish record: %s", result)
    return 0


def cmd_plugin_pull(args: argparse.Namespace) -> int:
    """s53 hub v1: fetch NAME from REMOTE, digest-verify the received priors/
    tree, and install through the standard s46 install path."""
    result = plugin_mod.plugin_pull(Path.cwd(), args.name, args.remote)
    logger.info("pull record: %s", result)
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
    # s46: pack-first scaffold; repeatable, first match wins
    p_init.add_argument("--plugin", action="append", default=[], metavar="PACKDIR",
                      help="install pack dir PACKDIR, then scaffold pack-first (repeatable)")
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

    p_harvest = sub.add_parser("harvest", help="close a season into a ledger record (step 4)")
    p_harvest.add_argument("id", help="season id, e.g. s2")
    p_harvest.add_argument("--verdict", required=True,
                           choices=["WIN", "LOSS", "NEUTRAL", "INVALID"])
    p_harvest.add_argument("--implies", required=True)
    p_harvest.add_argument(
        "--band", default="",
        help="expected band for the season metric; recorded verbatim in the verdict row",
    )
    p_harvest.add_argument(
        "--observed", default="",
        help="observed result for the season metric; recorded verbatim in the verdict row",
    )
    p_harvest.add_argument(
        "--strict",
        action="store_true",
        help="pass the close check's verdict exit through: 0 VERIFIED, 1 DELTA, "
        "2 structural refusal (default: the check is logged and recorded; the "
        "close exits on the harvest)",
    )
    p_harvest.set_defaults(func=cmd_harvest)

    p_audit = sub.add_parser(
        "audit",
        help="reflect over the season ledger; append evidence-cited candidates (DESIGN 15)",
    )
    p_audit.add_argument(
        "--last", type=int, default=10, metavar="N",
        help="audit the last N seasons (default: 10)",
    )
    p_audit.add_argument(
        "--corpus", action="store_true",
        help="refresh the replay corpus matrix with tools/replay_corpus.py "
        "before ingesting; a failed runner aborts the audit (s30)",
    )
    p_audit.set_defaults(func=cmd_audit)

    # s58: epics as data (directive seq 5) -- the declaration + the rollup verb
    p_epics = sub.add_parser(
        "epics",
        help="epic rollup: id, season span, verdict rollup, title (.rumpun/epics.yaml)",
    )
    p_epics.add_argument(
        "--init", action="store_true",
        help="scaffold .rumpun/epics.yaml from the season yamls (never overwrites)",
    )
    p_epics.set_defaults(func=cmd_epics)

    # s56: the check verb wires the s55 artifact checker for the operator
    p_check = sub.add_parser(
        "check",
        help="independent artifact check of a closed season from its close commit",
    )
    p_check.add_argument("sid", help="season id, e.g. s54")
    p_check.add_argument("close_commit", help="season-close commit sha")
    p_check.add_argument(
        "--out-dir", type=Path, default=None,
        help="record output dir (default: the live ledger .rumpun/ledger)",
    )
    p_check.set_defaults(func=cmd_check)

    # s65: the operator release for a containment-blocked season start
    p_waive = sub.add_parser(
        "waive",
        help="append the waiver-<sid> ledger record releasing a blocked start",
    )
    p_waive.add_argument("sid", help="blocked season id, e.g. s64")
    p_waive.add_argument(
        "--reason", required=True,
        help="recorded verbatim in the waiver record body",
    )
    p_waive.set_defaults(func=cmd_waive)

    # s66: the campaign board (directive seq 7) -- four columns, no new
    # state file; NEED HUMAN cards carry the seq 8 four sentences
    p_kanban = sub.add_parser(
        "kanban",
        help="campaign board: backlog, doing, need-human, done (directive seq 7)",
    )
    p_kanban.set_defaults(func=cmd_kanban)

    # s46: the plugin group (the hub arc's install step)
    p_plugin = sub.add_parser(
        "plugin", help="pack tools: install a pack into the campaign, list installed packs"
    )
    plugin_sub = p_plugin.add_subparsers(dest="plugin_command", required=True)
    p_install = plugin_sub.add_parser(
        "install",
        help="digest-verify, lint-gate, and copy a pack's priors/ into plugins/<name>/",
    )
    p_install.add_argument("packdir", help="pack directory: manifest.yaml plus priors/")
    p_install.set_defaults(func=cmd_plugin_install)
    p_plist = plugin_sub.add_parser(
        "list", help="installed packs: name, version, digest"
    )
    p_plist.set_defaults(func=cmd_plugin_list)
    # s50: the distill — the flywheel's export, drafted for review
    p_distill = plugin_sub.add_parser(
        "distill",
        help="draft a pack of generalized priors from the campaign's proven gates",
    )
    p_distill.add_argument(
        "pack_name", help="pack name (^[a-z0-9][a-z0-9_-]*$)"
    )
    p_distill.add_argument(
        "--source",
        required=True,
        help="provenance note stored verbatim as the manifest source",
    )
    p_distill.set_defaults(func=cmd_plugin_distill)
    # s53: hub v1 — publish and pull move a pack over a git remote
    p_publish = plugin_sub.add_parser(
        "publish",
        help="lint-gate and digest-verify an installed pack, then push it to REMOTE",
    )
    p_publish.add_argument("name", help="installed pack name")
    p_publish.add_argument(
        "--remote", required=True, help="git remote URL or file path"
    )
    p_publish.set_defaults(func=cmd_plugin_publish)
    p_pull = plugin_sub.add_parser(
        "pull",
        help="fetch NAME from REMOTE, digest-verify the received tree, install "
        "(the s46 path)",
    )
    p_pull.add_argument("name", help="expected pack name in the remote's manifest")
    p_pull.add_argument(
        "--remote", required=True, help="git remote URL or file path"
    )
    p_pull.set_defaults(func=cmd_plugin_pull)

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
        "approve", help="approve a drafted evolution; appends the ledger approval record",
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
        help="contain an applied season; on_reject policy is recorded in the ledger (P33)",
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
            evolve_mod.EvolveError, akar.AkarError, audit_mod.AuditError,
            plugin_mod.PluginError, epics_mod.EpicsError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
