#!/usr/bin/env python3
"""Cold-start check: the documented quickstart, end to end, in a temp dir (s38 w1).

External-task verification for the residual the usefulness-decade-3 audit
names first: "External task value remains unmeasured." A fresh operator path
through README.md's quickstart runs for real: init, minimal edit, lint,
season start, harvest, audit -- then the loop closes: the audit's record is
verified on disk, evolve plan drafts seasons/s2.yaml from the closed s1 (the
loop's defining step), the draft is minimally edited and linted, and s2 runs
and harvests against the same stub model route. The stub is a sh script that
appends one results row and exits 0. No network, no quota, no real model.
The repo's own campaign ledger is never touched; the whole run lives in one
temp dir that survives for inspection and is logged at the end, PASS or FAIL.

Steps in order; the first failure stops the run with a nonzero exit:
  1 rumpun init <dir>    scaffold exists (rumpun.yaml, seasons/, prompts/, ledger/, runs/)
  2 edit in process      stub route into rumpun.yaml and benih routes in s1.yaml
  3 rumpun lint          exits 0 on the edited season
  4 rumpun season start  runs s1 to completed; every benih exits 0
  5 rumpun harvest s1    ledger record s1-harvest plus the season verdict row
  6 rumpun audit         the audit-1 record lands in ledger/
  7 read ledger            the audit-1 record exists (the reflection is on disk)
  8 rumpun evolve plan   drafts seasons/s2.yaml from parent s1
  9 edit s2 + lint       stub routes, primary_change band, audit-1 citation; lint exits 0
 10 rumpun season start  runs s2 to completed against the same stub route
 11 rumpun harvest s2    ledger record s2-harvest plus the s2 verdict row

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
import hashlib
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

S1_IMPLIES = "the stub season ran end to end"
S2_IMPLIES = "the audit-seeded s2 season ran end to end"


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

    season = project / ".rumpun" / "seasons" / "s1.yaml"
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
        for rel in ("rumpun.yaml", "seasons", "prompts", "ledger", "runs")
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
    season = (project / ".rumpun" / "seasons" / "s1.yaml").read_text(encoding="utf-8")
    if season.count("route: stub") != 2:
        logger.error("STEP 2 FAIL: benih routes are not both 'route: stub'")
        return False
    logger.info("STEP 2 PASS: stub route and operator fills written (stub: %s)", stub)
    return True


def _step_lint(project: Path) -> bool:
    """Step 3: lint passes on the edited season (README command, exit 0)."""
    proc = _run_cli(project, STEP_TIMEOUT_S, "lint", ".rumpun/seasons/s1.yaml")
    if proc.returncode != 0:
        logger.error(
            "STEP 3 FAIL: rumpun lint .rumpun/seasons/s1.yaml (rc=%d)",
            proc.returncode,
        )
        _log_output(proc)
        return False
    logger.info("STEP 3 PASS: rumpun lint .rumpun/seasons/s1.yaml: exit 0")
    return True


def _step_start(project: Path, sid: str, step: str) -> bool:
    """Steps 4/10: season start runs the stub season to completed."""
    proc = _run_cli(
        project,
        START_TIMEOUT_S,
        "season",
        "start",
        f".rumpun/seasons/{sid}.yaml",
        "--json",
    )
    if proc.returncode != 0:
        logger.error(
            "STEP %s FAIL: rumpun season start %s (rc=%d)", step, sid, proc.returncode
        )
        _log_output(proc)
        return False
    try:
        state = json.loads(proc.stdout)
    except ValueError:
        logger.exception("STEP %s FAIL: season start --json printed no JSON object", step)
        _log_output(proc)
        return False
    if state.get("status") != "completed":
        logger.error(
            "STEP %s FAIL: season %s status %r, expected completed",
            step,
            sid,
            state.get("status"),
        )
        return False
    agents = state.get("agents") or {}
    bad = {
        name: (snap.get("state"), snap.get("exit_code"))
        for name, snap in agents.items()
        if snap.get("state") != "exited" or snap.get("exit_code") != 0
    }
    if bad:
        logger.error("STEP %s FAIL: benih not all exited 0: %s", step, bad)
        return False
    logger.info(
        "STEP %s PASS: rumpun season start %s: completed, every benih exited 0",
        step,
        sid,
    )
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


def _step_harvest(project: Path, sid: str, step: str, implies: str) -> bool:
    """Steps 5/11: harvest marks the verdict: ledger record plus the season row."""
    proc = _run_cli(
        project,
        STEP_TIMEOUT_S,
        "harvest",
        sid,
        "--verdict",
        "WIN",
        "--implies",
        implies,
    )
    if proc.returncode != 0:
        logger.error("STEP %s FAIL: rumpun harvest %s (rc=%d)", step, sid, proc.returncode)
        _log_output(proc)
        return False
    records = list((project / ".rumpun" / "ledger").glob(f"*_{sid}-harvest.md"))
    if len(records) != 1:
        logger.error(
            "STEP %s FAIL: no single ledger record declaring %s-harvest", step, sid
        )
        return False
    if f"id: {sid}-harvest" not in records[0].read_text(encoding="utf-8"):
        logger.error("STEP %s FAIL: record %s lacks the id line", step, records[0].name)
        return False
    verdicts = project / ".rumpun" / "runs" / sid / "verdicts.jsonl"
    if not verdicts.is_file():
        logger.error("STEP %s FAIL: %s missing after harvest", step, verdicts)
        return False
    try:
        rows = _read_jsonl(verdicts)
    except ValueError:
        logger.exception("STEP %s FAIL: verdicts.jsonl unreadable", step)
        return False
    if not any(r.get("season") == sid and r.get("verdict") == "WIN" for r in rows):
        logger.error(
            "STEP %s FAIL: no season row (%s, WIN) in verdicts.jsonl", step, sid
        )
        return False
    logger.info(
        "STEP %s PASS: harvest %s: ledger record %s, verdict row WIN",
        step,
        sid,
        records[0].name,
    )
    return True


def _step_audit(project: Path) -> bool:
    """Step 6: audit runs and lands the audit-1 record in ledger/."""
    proc = _run_cli(project, STEP_TIMEOUT_S, "audit")
    if proc.returncode != 0:
        logger.error("STEP 6 FAIL: rumpun audit (rc=%d)", proc.returncode)
        _log_output(proc)
        return False
    records = list((project / ".rumpun" / "ledger").glob("*_audit-1.md"))
    if len(records) != 1:
        logger.error("STEP 6 FAIL: no single ledger record declaring audit-1")
        return False
    if "id: audit-1" not in records[0].read_text(encoding="utf-8"):
        logger.error("STEP 6 FAIL: record %s lacks the id line", records[0].name)
        return False
    logger.info("STEP 6 PASS: rumpun audit: record %s landed", records[0].name)
    return True


def _step_audit_record(project: Path) -> bool:
    """Step 7: the audit-1 record from step 6 exists in ledger/ (read-only recheck)."""
    records = list((project / ".rumpun" / "ledger").glob("*_audit-1.md"))
    if len(records) != 1:
        logger.error("STEP 7 FAIL: no single ledger record declaring audit-1")
        return False
    if "id: audit-1" not in records[0].read_text(encoding="utf-8"):
        logger.error("STEP 7 FAIL: record %s lacks the id line", records[0].name)
        return False
    logger.info("STEP 7 PASS: audit-1 record %s exists in ledger/", records[0].name)
    return True


def _ledger_digest(record: Path) -> str:
    """sha256 hex of the ledger record body, recomputed exactly as lint does.

    Mirrors lint._citation_resolves: the body is lines[4:-1] joined with new
    lines and the final line digests those utf-8 bytes; a citation resolves
    only against this digest (full or a unique prefix of >= 8 chars).
    """
    lines = record.read_text(encoding="utf-8").splitlines()
    if len(lines) < 6 or not lines[-1].startswith("sha256: "):
        msg = f"ledger record {record} lacks the sha256 trailer"
        raise ValueError(msg)
    body = "\n".join(lines[4:-1])
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _step_evolve(project: Path) -> bool:
    """Step 8: evolve plan drafts seasons/s2.yaml from the closed s1 parent."""
    proc = _run_cli(project, STEP_TIMEOUT_S, "evolve", "plan", ".rumpun/seasons/s1.yaml")
    if proc.returncode != 0:
        logger.error(
            "STEP 8 FAIL: rumpun evolve plan .rumpun/seasons/s1.yaml (rc=%d)",
            proc.returncode,
        )
        _log_output(proc)
        return False
    draft = project / ".rumpun" / "seasons" / "s2.yaml"
    if not draft.is_file():
        logger.error("STEP 8 FAIL: draft %s missing after evolve plan", draft)
        return False
    text = draft.read_text(encoding="utf-8")
    if "id: s2" not in text or "parent: s1" not in text:
        logger.error("STEP 8 FAIL: draft %s lacks the id: s2 / parent: s1 lines", draft)
        return False
    logger.info("STEP 8 PASS: rumpun evolve plan: drafted %s from s1", draft)
    return True


def _edit_draft(project: Path) -> None:
    """Step 9 edit: the s2 operator fill, minimal, after evolve plan.

    evolve copies the parent benih verbatim, so the stub routes normally
    carry over from s1; the glm-5.2/fable substitution from s1's edit stays
    as the guard for a drifted draft. lint requires the primary_change band
    fields the skeleton ships empty. The audit-1 citation is what makes the
    reflection the seed of the season, and a citation that does not resolve
    fails lint, which is the loop's own gate.
    """
    ledger_dir = project / ".rumpun" / "ledger"
    records = sorted(ledger_dir.glob("*_audit-1.md"))
    if len(records) != 1:
        msg = f"expected exactly one audit-1 record in {ledger_dir}, found {len(records)}"
        raise ValueError(msg)
    digest = _ledger_digest(records[0])

    draft = project / ".rumpun" / "seasons" / "s2.yaml"
    text = draft.read_text(encoding="utf-8")
    if text.count("route: stub") != 2:
        text = _sub(text, "route: glm-5.2", "route: stub", "benih a1 route")
        text = _sub(text, "route: fable", "route: stub", "benih a2 route")
    text = _sub(
        text,
        'baseline: ""',
        'baseline: "s1 stub season completed end to end"',
        "primary_change.baseline",
    )
    text = _sub(
        text,
        'expected_band: ""',
        'expected_band: "WIN if s2 completes with every benih exited 0"',
        "primary_change.expected_band",
    )
    text = _sub(
        text,
        'rollback: ""',
        'rollback: "restore seasons/s1.yaml as the live season"',
        "primary_change.rollback",
    )
    text = _sub(
        text,
        'eval_window: ""',
        'eval_window: "the s2 run itself (runs/s2 artifacts)"',
        "primary_change.eval_window",
    )
    text = _sub(
        text,
        "  evidence: []",
        f"  evidence:\n    - ledger:audit-1@{digest}",
        "methodology.evidence",
    )
    draft.write_text(text, encoding="utf-8")


def _step_edit_s2(project: Path) -> bool:
    """Step 9: minimally edit the drafted s2, then lint it (exit 0 required)."""
    try:
        _edit_draft(project)
    except Exception:
        logger.exception("STEP 9 FAIL: minimal edit of the drafted s2")
        return False
    proc = _run_cli(project, STEP_TIMEOUT_S, "lint", ".rumpun/seasons/s2.yaml")
    if proc.returncode != 0:
        logger.error(
            "STEP 9 FAIL: rumpun lint .rumpun/seasons/s2.yaml (rc=%d)",
            proc.returncode,
        )
        _log_output(proc)
        return False
    logger.info(
        "STEP 9 PASS: s2 edited (stub routes, primary_change band, audit-1 citation); "
        "rumpun lint .rumpun/seasons/s2.yaml: exit 0"
    )
    return True


def main(argv: list[str] | None = None) -> int:
    """Run the eleven quickstart steps; first failure stops with a nonzero exit."""
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
        ("4", "season start", lambda: _step_start(project, "s1", "4")),
        ("5", "harvest", lambda: _step_harvest(project, "s1", "5", S1_IMPLIES)),
        ("6", "audit", lambda: _step_audit(project)),
        ("7", "audit record", lambda: _step_audit_record(project)),
        ("8", "evolve plan", lambda: _step_evolve(project)),
        ("9", "edit s2 + lint", lambda: _step_edit_s2(project)),
        ("10", "season start", lambda: _step_start(project, "s2", "10")),
        ("11", "harvest", lambda: _step_harvest(project, "s2", "11", S2_IMPLIES)),
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
        logger.info("COLDSTART CHECK: %d/%d steps PASS", len(steps), len(steps))
        return 0
    logger.error("COLDSTART CHECK: FAIL; temp dir kept for inspection")
    return 1


if __name__ == "__main__":
    sys.exit(main())
