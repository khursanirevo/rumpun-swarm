"""s54 w1 verification: evolve._render emits writers: from a benih: parent.

Runs the real render function on the real s53.yaml (read-only), writes the
render to /tmp for inspection, and gates on: writers: key present exactly
once, no top-level benih: key left, id/parent rewritten, and the writer
entries and budget lines carried over unchanged.
"""

import logging
import re
import sys
from pathlib import Path

from rumpun import evolve

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("w1-verify")

PARENT = Path("/mnt/data/work/rumpun/.rumpun/seasons/s53.yaml")
OUT = Path("/tmp/s54w1/s55-render-check.yaml")


def main() -> int:
    text = evolve._render(PARENT, "s53", "s55")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    lines = text.splitlines()
    top_level = [ln for ln in lines if ln and not ln[0].isspace()]
    parent_lines = PARENT.read_text(encoding="utf-8").splitlines()
    def name_count(t: list[str]) -> int:
        return sum(1 for ln in t if re.match(r"^- name:", ln))

    def budget_count(t: list[str]) -> int:
        return sum(1 for ln in t if re.match(r"^(\s*)budget: \{minutes:", ln))
    checks = {
        "writers key present exactly once": sum(1 for ln in lines if ln == "writers:") == 1,
        "no top-level benih key": all(ln != "benih:" for ln in top_level),
        "no benih anywhere at top level": all("benih" not in ln for ln in top_level),
        "id rewritten to s55": "id: s55" in lines,
        "parent rewritten to s53": "parent: s53" in lines,
        "writer entries preserved": name_count(lines) == name_count(parent_lines),
        "budget lines preserved": budget_count(lines) == budget_count(parent_lines),
        "trailing newline": text.endswith("\n"),
    }
    failed = {k: v for k, v in checks.items() if v is not True}
    for name, passed in checks.items():
        logger.info("%s: %s", name, "ok" if passed is True else "FAIL")
    if failed:
        return 1
    logger.info("render check passed; output at %s", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
