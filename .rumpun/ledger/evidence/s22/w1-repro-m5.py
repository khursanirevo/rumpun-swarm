"""M5 repro: failed seasons record "failed" and the season verbs exit nonzero.

Part A (engine): _finalize("completed") with failing/crashed agents records
status "failed"; all-exited-0 and terminated-only seasons stay "completed"
(H9 preserved); rule statuses (stopped_operator) survive with a failed agent
present.
Part B (mapping): engine.status_exit_code maps known statuses and treats
unknown statuses as unhealthy (exit 1).
Part C (end to end): `rumpun season start` on a season whose agents fail
exits nonzero and records "failed"; the same season's status/show/stop verbs
exit nonzero; the all-exit-0 control season exits 0 and records
"completed".

Usage: python3 repro_m5_failed_exit.py <repo-copy-dir>
Exit 0 = green, 1 = red, 2 = script error.
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


def _ws(
    root: Path,
    sid: str,
    name: str,
    *,
    exit_code: str | None,
    terminated: bool = False,
) -> None:
    """One terminal-agent workspace: state.json + optional exit/terminated."""
    ws = root / "rimba" / sid / name
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
    season = root / "rimba" / sid / "_season"
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
    if not hasattr(engine, "status_exit_code"):
        logger.warning("SKIP Part B: engine.status_exit_code absent (pre-fix copy)")
    else:
        for status in ("completed", "stopped_operator", "running"):
            checks.append(
                (f"exit_code('{status}') == 0", engine.status_exit_code(status) == 0)
            )
        for status in ("failed", "stopped_stall", "stopped_budget", "mystery-status"):
            checks.append(
                (f"exit_code('{status}') == 1", engine.status_exit_code(status) == 1)
            )

    # --- Part C: end-to-end verb honesty --------------------------------------
    def build_project(routes_value: str) -> Path:
        proj = Path(tempfile.mkdtemp()) / "proj"
        root = proj / ".rumpun"
        (root / "musim").mkdir(parents=True)
        (root / "prompts" / "dev").mkdir(parents=True)
        (root / "rumpun.yaml").write_text(
            "autonomy:\n"
            "  stage: manual\n"
            "  invariants: [goal_immutable, budget_cap, falsify_required]\n"
            "routes:\n"
            f'  glm: "{routes_value}"\n',
            encoding="utf-8",
        )
        (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
        (root / "musim" / "s1.yaml").write_text(
            "id: s1\n"
            'goal: "fixture"\n'
            'metric: "m"\n'
            "mode: fight\n"
            "methodology:\n"
            '  approach: "x"\n'
            "  evidence: []\n"
            "  primary_change:\n"
            "    type: add\n"
            "    node: execute\n"
            '    baseline: "b"\n'
            '    expected_band: "WIN if x"\n'
            '    rollback: "git revert"\n'
            '    eval_window: "s1"\n'
            "  pipeline:\n"
            "    - phase: execute\n"
            "      primitive: execute\n"
            "      agents: benih\n"
            "      prompt: prompts/dev/dummy.md\n"
            "      writes: results.jsonl\n"
            "benih:\n"
            "  - name: w1\n"
            "    route: glm\n"
            "    prompt: prompts/dev/dummy.md\n"
            "    knowledge: none\n"
            "    budget: {minutes: 1}\n"
            "  - name: w2\n"
            "    route: glm\n"
            "    prompt: prompts/dev/dummy.md\n"
            "    knowledge: none\n"
            "    budget: {minutes: 1}\n"
            "stop:\n"
            '  "on": [all_exited]\n',
            encoding="utf-8",
        )
        return root

    def run_verb(root: Path, *argv: str) -> int:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo / "src")
        proc = subprocess.run(
            [sys.executable, "-m", "rumpun", *argv],
            cwd=str(root.parent),
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

    fail_root = build_project("cat {prompt} | false")
    ok_root = build_project("cat {prompt} | true")

    rc_start_fail = run_verb(
        fail_root, "season", "start", str(fail_root / "musim" / "s1.yaml")
    )
    checks.append(("e2e failed season: start exits 1", rc_start_fail == 1))
    state = json.loads(
        (fail_root / "rimba" / "s1" / "_season" / "state.json").read_text(encoding="utf-8")
    )
    checks.append(("e2e failed season: status recorded failed", state["status"] == "failed"))
    agent_states = {n: a["state"] for n, a in state.get("agents", {}).items()}
    checks.append(
        ("e2e failed season: agents recorded failed", set(agent_states.values()) == {"failed"})
    )

    checks.append(
        (
            "status verb exits 1 on failed season",
            run_verb(fail_root, "season", "status", "s1") == 1,
        )
    )
    checks.append(
        (
            "show verb exits 1 on failed season",
            run_verb(fail_root, "season", "show", "s1") == 1,
        )
    )
    checks.append(
        (
            "stop verb exits 1 on failed season",
            run_verb(fail_root, "season", "stop", "s1") == 1,
        )
    )

    rc_start_ok = run_verb(ok_root, "season", "start", str(ok_root / "musim" / "s1.yaml"))
    checks.append(("e2e control: start exits 0", rc_start_ok == 0))
    state_ok = json.loads(
        (ok_root / "rimba" / "s1" / "_season" / "state.json").read_text(encoding="utf-8")
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
    raise SystemExit(main())
