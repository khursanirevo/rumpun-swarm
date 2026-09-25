"""M1 repro: a RUNNING season renders byte-identically under a shifted clock.

Builds a running-season fixture (persisted state.json carries no agent
snaps), renders report.render_report and report.render_index twice with two
different monkeypatched time.time values, and asserts byte-identical pages
plus a footer hash equal to the sha256 of the state.json bytes the page
rendered from.

Green on the M1 fix (report renders from persisted state only). Red on the
pre-fix code: read_status recomputes agent snaps from /proc and the clock,
so the two renders embed different "seconds" cells and drift.

Usage: python3 repro_m1_deterministic.py <repo-copy-dir>
Exit 0 = green, 1 = red, 2 = script error.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
import tempfile
from pathlib import Path
from unittest import mock

repo = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repo / "src"))

from rumpun import report  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("repro.m1.determinism")

STATE = {
    "id": "s99",
    "status": "running",
    "started_at": 1789420800.0,
    "stall_s": 2700.0,
    "budget_s": 60.0,
    "spawned": {"w1": {"pid": 999999, "proc_start": 12345}},
}

GOAL = 'id: s99\ngoal: "repro fixture season"\nmetric: "m"\n'


def build_fixture(root: Path) -> None:
    (root / "musim").mkdir(parents=True)
    (root / "musim" / "s99.yaml").write_text(GOAL, encoding="utf-8")
    season = root / "rimba" / "s99"
    (season / "_season").mkdir(parents=True)
    (season / "_season" / "state.json").write_text(
        json.dumps(STATE, indent=2) + "\n", encoding="utf-8"
    )
    ws = season / "w1"
    ws.mkdir()
    (ws / "state.json").write_text(
        json.dumps(
            {
                "name": "w1",
                "route": "glm",
                "cmd": "cat prompt.md",
                "pid": 999999,
                "proc_start": 12345,
                "started_at": 1789420800.0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ws / "agent.log").write_text(
        b'{"message":{"content":[{"type":"tool_use","name":"Read"}]}}\n'.decode(),
        encoding="utf-8",
    )


def render_both(root: Path, clock: float, tag: str) -> tuple[bytes, bytes]:
    """Render the season page and the landing page under one clock value."""
    with mock.patch("time.time", return_value=clock):
        page_path = report.render_report(root, "s99")
        index_path = report.render_index(root)
    page = page_path.read_bytes()
    index = index_path.read_bytes()
    logger.info(
        "%s: page %d bytes sha %s, index %d bytes sha %s",
        tag,
        len(page),
        hashlib.sha256(page).hexdigest()[:12],
        len(index),
        hashlib.sha256(index).hexdigest()[:12],
    )
    return page, index


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "proj" / ".rumpun"
        build_fixture(root)
        page1, index1 = render_both(root, clock=1_900_000_000.0, tag="clock T1")
        page2, index2 = render_both(root, clock=1_900_000_400.0, tag="clock T2")

        checks: list[tuple[str, bool]] = []
        checks.append(("season page byte-identical across clocks", page1 == page2))
        checks.append(("landing page byte-identical across clocks", index1 == index2))

        footer_hash = re.search(rb"state sha256:([0-9a-f]{12})", page1)
        raw = (root / "rimba" / "s99" / "_season" / "state.json").read_bytes()
        checks.append(
            (
                "footer hash covers the rendered state.json bytes",
                footer_hash is not None
                and footer_hash.group(1).decode()
                == hashlib.sha256(raw).hexdigest()[:12],
            )
        )
        status_row = b"Status" in page1 and b"running" in page1
        checks.append(("running season page shows persisted status", status_row))

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
