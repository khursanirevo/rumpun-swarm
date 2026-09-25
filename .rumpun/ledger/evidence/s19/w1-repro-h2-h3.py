"""s19 w1 repros for codex-review-2026-09-14 H2 + H3, against the PATCHED
engine copy in this scratch tree. Exits nonzero if any check fails.

H2: a stub agent whose pid slot was recycled (simulated by passing a wrong
proc_start) is NOT signaled, logs the mismatch WARNING, and gets no
terminated marker. Positive control: the correct proc_start signals and kills.

H3: a pwd route's agent.log records the workspace as its cwd, the standard
`cat {prompt}` route works from inside the workspace, exit files land, and
the season completes.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import tempfile
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRATCH / "src"))

from rumpun import engine  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stdout,
)
logger = logging.getLogger("s19w1.repro")


class Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def repro_h2(capture: Capture) -> bool:
    logger.info("--- H2: identity-checked termination ---")
    engine.logger.addHandler(capture)
    ws = Path(tempfile.mkdtemp(prefix="h2-ws-"))
    proc = subprocess.Popen(["/bin/sh", "-c", "sleep 30"], start_new_session=True)
    real = engine._proc_start_ticks(proc.pid)
    if real is None:
        logger.error("FAIL H2 setup: stub died at spawn")
        return False
    wrong = real + 12345
    engine._terminate(ws, proc.pid, wrong)
    alive_after = engine._proc_start_ticks(proc.pid) == real
    warned = any(
        rec.levelno == logging.WARNING
        and "identity mismatch" in rec.getMessage()
        and str(ws) in rec.getMessage()
        and str(wrong) in rec.getMessage()
        and str(real) in rec.getMessage()
        for rec in capture.records
    )
    marker_absent = not (ws / "terminated").exists()
    # positive control: the recorded identity signals and kills
    engine._terminate(ws, proc.pid, real)
    dead = engine._proc_start_ticks(proc.pid) is None
    proc.wait(timeout=5)
    logger.info(
        "H2 mismatch: not_signaled=%s warned=%s marker_absent=%s "
        "(pid %s, recorded start %s, live start %s)",
        alive_after, warned, marker_absent, proc.pid, wrong, real,
    )
    logger.info(
        "H2 control: signaled_and_dead=%s marker_written=%s",
        dead, (ws / "terminated").is_file(),
    )
    return alive_after and warned and marker_absent and dead


def repro_h3() -> bool:
    logger.info("--- H3: agents run inside their workspace ---")
    proj = Path(tempfile.mkdtemp(prefix="h3-proj-")) / ".rumpun"
    (proj / "musim").mkdir(parents=True)
    (proj / "prompt.md").write_text("H3 cwd probe prompt\n", encoding="utf-8")
    (proj / "rumpun.yaml").write_text(
        "routes:\n  stub: 'pwd'\n  stubcat: 'cat {prompt}'\n", encoding="utf-8",
    )
    season_path = proj / "musim" / "h3.yaml"
    season_path.write_text(
        'id: h3\n'
        'benih:\n'
        '  - name: w1\n    route: stub\n    prompt: prompt.md\n'
        '  - name: w2\n    route: stubcat\n    prompt: prompt.md\n'
        'stop:\n  "on": [all_exited]\n',
        encoding="utf-8",
    )
    state = engine.start_season(season_path, proj)
    ws1 = (proj / "rimba" / "h3" / "w1").resolve()
    ws2 = (proj / "rimba" / "h3" / "w2").resolve()
    cwd_logged = (ws1 / "agent.log").read_text(encoding="utf-8").strip()
    prompt_replayed = (ws2 / "agent.log").read_text(encoding="utf-8").strip()
    exits = [(ws1 / "exit").read_text(), (ws2 / "exit").read_text()]
    ok = (
        state["status"] == "completed"
        and cwd_logged == str(ws1)
        and prompt_replayed == "H3 cwd probe prompt"
        and exits == ["0", "0"]
    )
    logger.info(
        "H3: status=%s pwd_in_log=%s equals_workspace=%s cat_route_replayed_prompt=%s exits=%s",
        state["status"], cwd_logged, cwd_logged == str(ws1),
        prompt_replayed == "H3 cwd probe prompt", exits,
    )
    logger.info("H3 workspace path: %s", ws1)
    return ok


def main() -> int:
    capture = Capture()
    ok_h2 = repro_h2(capture)
    ok_h3 = repro_h3()
    logger.info("RESULT: H2=%s H3=%s", "PASS" if ok_h2 else "FAIL", "PASS" if ok_h3 else "FAIL")
    return 0 if ok_h2 and ok_h3 else 1


if __name__ == "__main__":
    raise SystemExit(main())
