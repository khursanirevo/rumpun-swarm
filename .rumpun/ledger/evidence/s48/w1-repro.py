"""M5 repro, re-sealed to current main (s48 w1; supersedes the s22 copy).

The s22 original bound to the legacy on-disk layout (rimba/ workspaces,
musim/ season docs) and to a season yaml that predates the falsify lint's
non-empty-reads rule. After the s45 English rename it died on its own
stale paths (FileNotFoundError at rimba/s1/_season/state.json) and the
replay matrix armed DRIFT (audit-36: exit 1 in 0.3s, assumption moved).
This re-seal keeps the s22 three-part shape and the fixture season
verbatim (RUMPUN_YAML_FAIL + SEASON_DUAL from tests/test_rumpun.py) and
rebinds the mechanics to current main (runs/ + seasons/ layout):

Part A (engine): _finalize("completed") with failing/crashed agents
records status "failed"; all-exited-0 and terminated-only seasons stay
"completed" (H9 preserved); rule statuses (stopped_operator) survive
with a failed agent present.
Part B (mapping): engine.status_exit_code maps known statuses; unknown
statuses are unhealthy (exit 1).
Part C (end to end): `rumpun season start` on a season whose both benih
fail (routes.glm = "false") exits nonzero and records "failed" with both
agents "failed"; the same season's status/show/stop verbs exit nonzero;
the all-exit-0 control season (RUMPUN_YAML) exits 0 and records
"completed" with status/stop exiting 0.

Usage: python3 repro_m5_failed_exit.py <repo-copy-dir>
Exit 0 = green, 1 = red (behavioral), 2 = script error (not a red).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repo / "src"))

from rumpun import engine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("repro.m5")

# Fixtures verbatim from tests/test_rumpun.py (fixture season unchanged).
RUMPUN_YAML_FAIL = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "false"
"""

# The all-exit-0 control project (RUMPUN_YAML in tests/test_rumpun.py).
RUMPUN_YAML = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "cat {prompt} | true"
"""

# Fixture season unchanged: SEASON_DUAL verbatim (benih alpha + beta; the
# execute node's reads: results.jsonl satisfies the falsify lint preflight).
SEASON_DUAL = """\
id: s1
goal: "fixture"
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
    rollback: "git revert"
    eval_window: "s1"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
      reads: results.jsonl
benih:
  - name: alpha
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 1}
  - name: beta
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 1}
stop:
  "on": [all_exited]
"""


def _ws(
    root: Path,
    sid: str,
    name: str,
    *,
    exit_code: str | None,
    terminated: bool = False,
) -> None:
    """One terminal-agent workspace under the s45 runs/ layout."""
    ws = root / "runs" / sid / name
    ws.mkdir(parents=True)
    (ws / "state.json").write_text(
        json.dumps(
            {
                "name": name,
                "route": "glm",
                "cmd": "cat prompt.md",
                "pid": 999999,
                "proc_start": None,
                "started_at": 1789420800.0,
            }
        ),
        encoding="utf-8",
    )
    if exit_code is not None:
        (ws / "exit").write_text(exit_code, encoding="utf-8")
        return
    if terminated:
        (ws / "terminated").write_text("terminated\n", encoding="utf-8")


def _season_state(root: Path, sid: str, names: list[str]) -> None:
    season = root / "runs" / sid / "_season"
    season.mkdir(parents=True)
    (season / "state.json").write_text(
        json.dumps(
            {
                "id": sid,
                "status": "running",
                "started_at": 1789420800.0,
                "stall_s": 2700.0,
                "budget_s": 60.0,
                "spawned": {name: {"pid": 999999, "proc_start": None} for name in names},
            }
        ),
        encoding="utf-8",
    )


def build_project(routes_yaml: str, under: Path) -> Path:
    """The s45 project shape (tests' _write_proj): seasons/, ledger/, runs/."""
    proj = under / "proj"
    root = proj / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    (root / "runs").mkdir()
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(routes_yaml, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    (root / "seasons" / "s1.yaml").write_text(SEASON_DUAL, encoding="utf-8")
    return root


def main() -> int:
    checks: list[tuple[str, bool]] = []
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name) / "proj" / ".rumpun"

    # --- Part A: finalize reclassification -----------------------------------
    def run_case(tag: str, agents: dict[str, str | None], status_arg: str) -> str:
        sid = f"s{tag}"
        _season_state(root, sid, list(agents))
        for name, code in agents.items():
            terminated = code == "T"
            _ws(
                root,
                sid,
                name,
                exit_code=None if terminated else code,
                terminated=terminated,
            )
        state = engine._finalize(root, sid, status_arg, {})
        return str(state["status"])

    checks.append(
        (
            "both failed -> failed",
            run_case("ff", {"w1": "3", "w2": "4"}, "completed") == "failed",
        )
    )
    checks.append(
        (
            "mixed exit0+failed -> failed",
            run_case("mf", {"w1": "0", "w2": "3"}, "completed") == "failed",
        )
    )
    checks.append(
        (
            "crashed(no exit, dead pid) + exited -> failed",
            run_case("cr", {"w1": None, "w2": "0"}, "completed") == "failed",
        )
    )
    checks.append(
        (
            "all exited 0 -> completed",
            run_case("ok", {"w1": "0", "w2": "0"}, "completed") == "completed",
        )
    )
    checks.append(
        (
            "terminated-only -> completed (H9 preserved)",
            run_case("term", {"w1": "T", "w2": "T"}, "completed") == "completed",
        )
    )
    checks.append(
        (
            "stopped_operator keeps rule status with a failed agent",
            run_case("op", {"w1": "3"}, "stopped_operator") == "stopped_operator",
        )
    )

    # --- Part B: the status -> exit-code mapping ------------------------------
    for status in ("completed", "stopped_operator", "running"):
        checks.append(
            (f"exit_code('{status}') == 0", engine.status_exit_code(status) == 0)
        )
    for status in ("failed", "stopped_stall", "stopped_budget", "mystery-status"):
        checks.append(
            (f"exit_code('{status}') == 1", engine.status_exit_code(status) == 1)
        )

    # --- Part C: end-to-end verb honesty --------------------------------------
    def run_verb(proj_root: Path, *argv: str) -> int:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo / "src")
        proc = subprocess.run(
            [sys.executable, "-m", "rumpun", *argv],
            cwd=str(proj_root.parent),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        logger.info(
            "verb %s -> rc=%d stderr-tail: %s",
            argv,
            proc.returncode,
            (proc.stderr or "")[-300:].replace("\n", " | "),
        )
        return proc.returncode

    with tempfile.TemporaryDirectory() as ctmp:
        base = Path(ctmp)
        fail_root = build_project(RUMPUN_YAML_FAIL, base / "fail")
        ok_root = build_project(RUMPUN_YAML, base / "ok")

        rc_start_fail = run_verb(
            fail_root, "season", "start", str(fail_root / "seasons" / "s1.yaml")
        )
        logger.info("fail-season start rc=%d", rc_start_fail)
        checks.append(("e2e failed season: start exits nonzero", rc_start_fail != 0))
        state = json.loads(
            (fail_root / "runs" / "s1" / "_season" / "state.json").read_text(
                encoding="utf-8"
            )
        )
        checks.append(("e2e failed season: status recorded failed", state["status"] == "failed"))
        agents = state.get("agents") or {}
        agent_states = {
            name: (agents.get(name) or {}).get("state") for name in ("alpha", "beta")
        }
        expected = {"alpha": "failed", "beta": "failed"}
        checks.append(
            ("e2e failed season: agents recorded failed", agent_states == expected)
        )

        checks.append(
            (
                "status verb exits nonzero on failed season",
                run_verb(fail_root, "season", "status", "s1") != 0,
            )
        )
        checks.append(
            (
                "show verb exits nonzero on failed season",
                run_verb(fail_root, "season", "show", "s1") != 0,
            )
        )
        checks.append(
            (
                "stop verb exits nonzero on failed season",
                run_verb(fail_root, "season", "stop", "s1") != 0,
            )
        )

        rc_start_ok = run_verb(
            ok_root, "season", "start", str(ok_root / "seasons" / "s1.yaml")
        )
        checks.append(("e2e control: start exits 0", rc_start_ok == 0))
        state_ok = json.loads(
            (ok_root / "runs" / "s1" / "_season" / "state.json").read_text(
                encoding="utf-8"
            )
        )
        checks.append(("e2e control: status completed", state_ok["status"] == "completed"))
        checks.append(
            (
                "status verb exits 0 on completed season",
                run_verb(ok_root, "season", "status", "s1") == 0,
            )
        )
        checks.append(
            (
                "stop verb exits 0 on completed season",
                run_verb(ok_root, "season", "stop", "s1") == 0,
            )
        )

    tmp.cleanup()
    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        logger.info("%s: %s", "PASS" if ok else "FAIL", name)
    if failed:
        logger.error("RED: %d/%d checks failed: %s", len(failed), len(checks), failed)
        return 1
    logger.info("GREEN: %d/%d checks passed", len(checks), len(checks))
    return 0


if __name__ == "__main__":
    try:
        _code = main()
    except Exception:
        # A moved assumption (crash) must never masquerade as a behavioral
        # red; this is the exit-2 lane the audit's DRIFT arming reads.
        logger.exception("script error (exit 2), not a behavioral red")
        _code = 2
    raise SystemExit(_code)
