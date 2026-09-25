"""s54 w1: apply the exact s54 edits to the workspace copies of cli.py and evolve.py.

Every pair must occur in the copy exactly the stated number of times; the
script exits 1 and changes nothing when any count mismatches (no silent
partial edits).
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("w1-edit")

WS = Path(__file__).resolve().parent

CLI_EDITS: list[tuple[str, str, int]] = [
    # deliverable 4: the direct verb resolves the directives lane through the
    # s45 paths resolver (ledger/ when present, akar/ legacy fallback)
    (
        "from rumpun import __version__, akar, collab, engine, scaffold, yamlio",
        "from rumpun import __version__, akar, collab, engine, paths, scaffold, yamlio",
        1,
    ),
    (
        '    lane = {\n'
        '        "file": str(root / "akar" / "directives.jsonl"),\n'
        '        "lock": str(root / "akar" / "directives.lock"),\n'
        "    }",
        "    ledger = paths.ledger_dir(root)\n"
        "    lane = {\n"
        '        "file": str(ledger / "directives.jsonl"),\n'
        '        "lock": str(ledger / "directives.lock"),\n'
        "    }",
        1,
    ),
    # deliverable 2: harvest help becomes English; akar leaves the strings
    (
        "tuai: close a season into akar (step 4)",
        "close a season into a ledger record (step 4)",
        1,
    ),
    ("becomes an akar record", "becomes a ledger record", 1),
    ("akar record %s", "ledger record %s", 3),
    ("is recorded in akar.", "is recorded as a ledger record.", 1),
    (
        "the on_reject policy records in akar; code-level",
        "the on_reject policy is recorded as a ledger record; code-level",
        1,
    ),
    (
        "on_reject policy records in akar (P33)",
        "on_reject policy is recorded in the ledger (P33)",
        1,
    ),
    ("appends the akar approval record", "appends the ledger approval record", 1),
    # deliverable 2: the reject/rollback strings state the real paths
    ("musim/rejected/", ".rumpun/seasons/rejected/", 4),
    ("musim/<sid>.yaml moves to", ".rumpun/seasons/<sid>.yaml moves to", 1),
    # the season theme: musim leaves the audit help too
    ("audit the last N musim seasons (default: 10)", "audit the last N seasons (default: 10)", 1),
]

EVOLVE_EDITS: list[tuple[str, str, int]] = [
    # deliverable 1: stall resume reads the writer table writers-first
    (
        '    benih = parent.get("benih")\n'
        "    if not isinstance(benih, list) or not benih:\n"
        '        msg = f"stopped_stall parent {parent_id} has no benih to re-size"',
        '    writers = parent.get("writers") or parent.get("benih")\n'
        "    if not isinstance(writers, list) or not writers:\n"
        '        msg = f"stopped_stall parent {parent_id} has no writer table to re-size"',
        1,
    ),
    ("    for entry in benih:\n", "    for entry in writers:\n", 1),
    (
        ': benih entries must be mappings"',
        ': writer entries must be mappings"',
        1,
    ),
    (
        ': benih budget.minutes "',
        ': writer budget.minutes "',
        1,
    ),
    (
        "    goal/metric/mode, the pipeline, benih, and stop are copied byte-identical\n"
        "    from the parent",
        "    goal/metric/mode, the pipeline, the writer table, and stop are copied\n"
        "    byte-identical from the parent, except the top-level benih: key renders\n"
        "    as writers: (the s54 schema rename; benih stays the read alias)",
        1,
    ),
    (
        '        if line.startswith(("id:", "parent:")):\n'
        "            continue  # rewritten above\n",
        '        if line.startswith(("id:", "parent:")):\n'
        "            continue  # rewritten above\n"
        '        if line.rstrip("\\n") == "benih:":\n'
        '            out.append("writers:\\n")\n'
        "            continue  # s54: drafts emit the writers key; benih stays the alias\n",
        1,
    ),
]


def apply(path: Path, edits: list[tuple[str, str, int]]) -> bool:
    text = path.read_text(encoding="utf-8")
    for old, _new, count in edits:
        found = text.count(old)
        if found != count:
            logger.error(
                "%s: expected %d occurrence(s), found %d: %r",
                path.name, count, found, old[:60],
            )
            return False
    for old, new, _count in edits:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    logger.info("%s: %d edit pair(s) applied", path.name, len(edits))
    return True


def main() -> int:
    ok = apply(WS / "cli.py", CLI_EDITS) and apply(WS / "evolve.py", EVOLVE_EDITS)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
