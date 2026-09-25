#!/usr/bin/env python3
"""Cold-start check: the documented quickstart, end to end, in a temp dir (s37 w1).

External-task verification for the residual the usefulness-decade-3 audit
names first: "External task value remains unmeasured." A fresh operator path
through README.md's quickstart runs for real: init, minimal edit, lint,
season start, harvest, audit, against a stub model route. The stub is a sh
script that appends one results row and exits 0. No network, no quota, no
real model. The repo's own campaign ledger is never touched; the whole run
lives in one temp dir that survives for inspection and is logged at the end,
PASS or FAIL.

Steps in order; the first failure stops the run with a nonzero exit:
  1 rumpun init <dir>    scaffold exists (rumpun.yaml, musim/, prompts/, akar/, rimba/)
  2 edit in process      stub route into rumpun.yaml and benih routes in s1.yaml
  3 rumpun lint          exits 0 on the edited season
  4 rumpun season start  runs to completed; every benih exits 0
  5 rumpun harvest s1    akar record s1-harvest plus the season verdict row
  6 rumpun audit         the audit-1 record lands in akar/

The CLI runs as `sys.executable -m rumpun` with cwd at the temp project, so
the checker exercises the rumpun package of the interpreter running it.

Usage: coldstart_check.py [--init-target DIR]
    --init-target DIR  fault injection: init into DIR makes step 1 fail
        honestly when DIR cannot take the scaffold. Later steps still run
        against the temp project, so the read-only failure is the case to
        exercise.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger("coldstart_check")

STEP_TIMEOUT_S = 60
START_TIMEOUT_S = 90

STUB_ROUTE = """\
#!/bin/sh
# coldstart stub model route (s37 w1): append one results row, exit 0.
# cwd is the benih workspace; the prompt path arrives as $1 and is ignored.
printf '{"experiment_id": "e1", "unit": "stub", "verdict": "ok"}\\n' >> results.jsonl
exit 0
"""

GOAL = "coldstart: the documented quickstart completes"
METRIC = "coldstart metric"


def _sub(text: str, old: str, new: str, what: str) -> str:
    """Replace the single `old` occurrence; raise when the anchor count is not 1.

    A missing anchor means the scaffold drifted from the documented shape,
    which is a defect this checker exists to catch, so it fails loudly.
    """
    count = text.count(old)
    if count != 1:
        msg = f"scaffold anchor {what!r} found {count} times (expected 1)"
        raise ValueError(msg)
    return text.replace(old, new)


def _sub_pattern(text: str, pattern: str, repl: str, what: str) -> str:
    """Regex variant of _sub; the lambda keeps repl free of backslash escapes."""
    text, n = re.subn(pattern, lambda _m: repl, text, count=1, flags=re.MULTILINE)
    if n != 1:
        msg = f"scaffold anchor {what!r} matched {n} times (expected 1)"
        raise ValueError(msg)
    return text


def _edit_campaign(project: Path, stub: Path) -> None:
    """Step 2: the fills README asks of the operator, routed to the stub."""
    cfg = project / ".rumpun" / "rumpun.yaml"
    text = cfg.read_text(encoding="utf-8")
    text = _sub(text, 'goal: ""', f'goal: "{GOAL}"', "campaign.goal")
    text = _sub(text, 'metric: ""', f'metric: "{METRIC}"', "campaign.metric")
    text = _sub(
        text,
        "campaign_cost_cap: null",
        "campaign_cost_cap: 10",
        "budget.campaign_cost_cap",
    )
    route_line = f"routes:\n  stub: 'sh {stub} {{prompt}}'"
    text = _sub_pattern(text, r"^routes:\s*\{\}.*$", route_line, "routes: {}")
    cfg.write_text(text, encoding="utf-8")

    season = project / ".rumpun" / "musim" / "s1.yaml"
    text = season.read_text(encoding="utf-8")
    text = _sub(text, 'goal: ""', f'goal: "{GOAL}"', "season goal")
    text = _sub(text, 'metric: ""', f'metric: "{METRIC}"', "season metric")
    text = _sub(text, "route: glm-5.2", "route: stub", "benih a1 route")
    text = _sub(text, "route: fable", "route: stub", "benih a2 route")
    season.write_text(text, encoding="utf-8")


def _run_cli(project: Path, timeout_s: int, *args: str) -> subprocess.CompletedProcess:
    """One rumpun CLI call: the checker's own interpreter, cwd at the project."""
    cmd = [sys.executable, "-m", "rumpun", *args]
    logger.info("run: (cd %s && %s)", project, " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=str(project),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


def _log_output(proc: subprocess.CompletedProcess) -> None:
    """Tail of captured streams on a failing step, indented under the FAIL line."""
    for name in ("stdout", "stderr"):
        text = (getattr(proc, name) or "").strip()
        if text:
            for line in text.splitlines()[-20:]:
                logger.error("  %s| %s", name[:3], " ".join(line.split())[:150])


def _scaffold_ok(project: Path) -> list[str]:
    """Missing scaffold entries under project/.rumpun; empty list means complete."""
    return [
        rel
        for rel in ("rumpun.yaml", "musim", "prompts", "akar", "rimba")
        if not (project / ".rumpun" / rel).exists()
    ]


def _step_init(project: Path, target: Path) -> bool:
    """Step 1: init the scaffold into target and check the documented layout."""
    proc = _run_cli(project, STEP_TIMEOUT_S, "init", str(target))
    if proc.returncode != 0:
        logger.error("STEP 1 FAIL: rumpun init %s (rc=%d)", target, proc.returncode)
        _log_output(proc)
        return False
    missing = _scaffold_ok(target)
    if missing:
        logger.error(
            "STEP 1 FAIL: rumpun init %s: scaffold incomplete, missing %s",
            target,
            ", ".join(missing),
        )
        return False
    logger.info("STEP 1 PASS: rumpun init %s: scaffold complete", target)
    return True


def _step_edit(project: Path) -> bool:
    """Step 2: write the stub route script and apply the operator fills."""
    stub = project / "stub_route.sh"
    try:
        stub.write_text(STUB_ROUTE, encoding="utf-8")
        _edit_campaign(project, stub)
    except Exception:
        logger.exception("STEP 2 FAIL: in-process edit of the scaffolded season")
        return False
    season = (project / ".rumpun" / "musim" / "s1.yaml").read_text(encoding="utf-8")
    if season.count("route: stub") != 2:
        logger.error("STEP 2 FAIL: benih routes are not both 'route: stub'")
        return False
    logger.info("STEP 2 PASS: stub route and operator fills written (stub: %s)", stub)
    return True


def _step_lint(project: Path) -> bool:
    """Step 3: lint passes on the edited season (README command, exit 0)."""
    proc = _run_cli(project, STEP_TIMEOUT_S, "lint", ".rumpun/musim/s1.yaml")
    if proc.returncode != 0:
        logger.error(
            "STEP 3 FAIL: rumpun lint .rumpun/musim/s1.yaml (rc=%d)",
            proc.returncode,
        )
        _log_output(proc)
        return False
    logger.info("STEP 3 PASS: rumpun lint .rumpun/musim/s1.yaml: exit 0")
    return True


def _step_start(project: Path) -> bool:
    """Step 4: season start runs the stub season to completed."""
    proc = _run_cli(
        project, START_TIMEOUT_S, "season", "start", ".rumpun/musim/s1.yaml", "--json"
    )
    if proc.returncode != 0:
        logger.error("STEP 4 FAIL: rumpun season start (rc=%d)", proc.returncode)
        _log_output(proc)
        return False
    try:
        state = json.loads(proc.stdout)
    except ValueError:
        logger.exception("STEP 4 FAIL: season start --json printed no JSON object")
        _log_output(proc)
        return False
    if state.get("status") != "completed":
        logger.error(
            "STEP 4 FAIL: season status %r, expected completed", state.get("status")
        )
        return False
    agents = state.get("agents") or {}
    bad = {
        name: (snap.get("state"), snap.get("exit_code"))
        for name, snap in agents.items()
        if snap.get("state") != "exited" or snap.get("exit_code") != 0
    }
    if bad:
        logger.error("STEP 4 FAIL: benih not all exited 0: %s", bad)
        return False
    logger.info("STEP 4 PASS: rumpun season start: completed, every benih exited 0")
    return True


def _read_jsonl(path: Path) -> list[dict]:
    """Parse a jsonl file; any unparseable non-blank line raises ValueError."""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            msg = f"unparseable line in {path}"
            raise ValueError(msg) from None
    return rows


def _step_harvest(project: Path) -> bool:
    """Step 5: harvest marks the verdict: akar record plus the season row."""
    proc = _run_cli(
        project,
        STEP_TIMEOUT_S,
        "harvest",
        "s1",
        "--verdict",
        "WIN",
        "--implies",
        "the stub season ran end to end",
    )
    if proc.returncode != 0:
        logger.error("STEP 5 FAIL: rumpun harvest s1 (rc=%d)", proc.returncode)
        _log_output(proc)
        return False
    records = list((project / ".rumpun" / "akar").glob("*_s1-harvest.md"))
    if len(records) != 1:
        logger.error("STEP 5 FAIL: no single akar record declaring s1-harvest")
        return False
    if "id: s1-harvest" not in records[0].read_text(encoding="utf-8"):
        logger.error("STEP 5 FAIL: record %s lacks the id line", records[0].name)
        return False
    verdicts = project / ".rumpun" / "rimba" / "s1" / "verdicts.jsonl"
    if not verdicts.is_file():
        logger.error("STEP 5 FAIL: %s missing after harvest", verdicts)
        return False
    try:
        rows = _read_jsonl(verdicts)
    except ValueError:
        logger.exception("STEP 5 FAIL: verdicts.jsonl unreadable")
        return False
    if not any(
        r.get("season") == "s1" and r.get("verdict") == "WIN" for r in rows
    ):
        logger.error("STEP 5 FAIL: no season row (s1, WIN) in verdicts.jsonl")
        return False
    logger.info(
        "STEP 5 PASS: harvest s1: akar record %s, verdict row WIN", records[0].name
    )
    return True


def _step_audit(project: Path) -> bool:
    """Step 6: audit runs and lands the audit-1 record in akar/."""
    proc = _run_cli(project, STEP_TIMEOUT_S, "audit")
    if proc.returncode != 0:
        logger.error("STEP 6 FAIL: rumpun audit (rc=%d)", proc.returncode)
        _log_output(proc)
        return False
    records = list((project / ".rumpun" / "akar").glob("*_audit-1.md"))
    if len(records) != 1:
        logger.error("STEP 6 FAIL: no single akar record declaring audit-1")
        return False
    if "id: audit-1" not in records[0].read_text(encoding="utf-8"):
        logger.error("STEP 6 FAIL: record %s lacks the id line", records[0].name)
        return False
    logger.info("STEP 6 PASS: rumpun audit: record %s landed", records[0].name)
    return True


def main(argv: list[str] | None = None) -> int:
    """Run the six quickstart steps; first failure stops with a nonzero exit."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(
        description="Run the README quickstart end to end in a temp dir.",
    )
    parser.add_argument(
        "--init-target",
        type=Path,
        default=None,
        help="fault injection: init into DIR; a read-only DIR fails step 1",
    )
    args = parser.parse_args(argv)
    project = Path(tempfile.mkdtemp(prefix="rumpun-coldstart-"))
    target = args.init_target.resolve() if args.init_target else project
    steps = [
        ("1", "init", lambda: _step_init(project, target)),
        ("2", "edit", lambda: _step_edit(project)),
        ("3", "lint", lambda: _step_lint(project)),
        ("4", "season start", lambda: _step_start(project)),
        ("5", "harvest", lambda: _step_harvest(project)),
        ("6", "audit", lambda: _step_audit(project)),
    ]
    ok = True
    for number, name, step in steps:
        try:
            if not step():
                ok = False
                break
        except subprocess.TimeoutExpired as exc:
            logger.error(
                "STEP %s (%s) FAIL: timed out: %s", number, name, " ".join(exc.cmd)
            )
            ok = False
            break
    logger.info("temp dir: %s", project)
    if ok:
        logger.info("COLDSTART CHECK: 6/6 steps PASS")
        return 0
    logger.error("COLDSTART CHECK: FAIL; temp dir kept for inspection")
    return 1


if __name__ == "__main__":
    sys.exit(main())
