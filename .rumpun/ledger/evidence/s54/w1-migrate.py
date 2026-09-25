"""s54 w1: migrate the stray directive from .rumpun/akar/ into the ledger (deliverable 4).

The pre-fix direct verb wrote .rumpun/akar/directives.jsonl while the
campaign's real history is .rumpun/ledger/directives.jsonl. Appends the one
stray record to the ledger file through collab.append_event (the same
LOCK_EX + line-count + one-write path the fixed verb uses; the count yields
max seq + 1), gates on a readback, then removes the stray files and the
empty akar/ directory (rmdir refuses when non-empty). Re-running after a
successful migration is a no-op.
"""

import logging
import sys
from pathlib import Path

from rumpun import collab

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("w1-migrate")

ROOT = Path("/mnt/data/work/rumpun/.rumpun")
STRAY = ROOT / "akar" / "directives.jsonl"
STRAY_LOCK = ROOT / "akar" / "directives.lock"
LEDGER = ROOT / "ledger" / "directives.jsonl"
LANE = {"file": str(LEDGER), "lock": str(ROOT / "ledger" / "directives.lock")}
RENAME_MARK = "finish the English rename"


def already_migrated() -> bool:
    """True when the ledger already carries the stray record's text."""
    try:
        events = collab.read_events(LANE)
    except collab.LaneError:
        return False
    return any(RENAME_MARK in str(e.get("text", "")) for e in events)


def main() -> int:
    if not STRAY.is_file():
        if already_migrated():
            logger.info("already migrated; nothing to do")
            return 0
        logger.error("stray file missing and no migrated copy in %s", LEDGER)
        return 1
    stray = collab.read_events({"file": str(STRAY), "lock": str(STRAY_LOCK)})
    if len(stray) != 1:
        logger.error("expected exactly 1 stray record, found %d; not guessing", len(stray))
        return 1
    record = stray[0]
    existing = collab.read_events(LANE)
    if any(str(record.get("text")) == str(e.get("text")) for e in existing):
        logger.info("already migrated; nothing to do")
        return 0
    expected_seq = max(int(e["seq"]) for e in existing) + 1
    collab.append_event(
        LANE,
        str(record.get("from", "operator")),
        {"text": record["text"], "status": record.get("status", "pending")},
    )
    readback = collab.read_events(LANE)
    migrated = [e for e in readback if e.get("text") == record["text"]]
    if len(migrated) != 1 or int(migrated[0]["seq"]) != expected_seq:
        logger.error("readback mismatch: expected seq %d, got %s", expected_seq, migrated)
        return 1
    logger.info("appended seq %d to %s", expected_seq, LEDGER)
    STRAY.unlink()
    STRAY_LOCK.unlink(missing_ok=True)
    STRAY.parent.rmdir()  # refuses when the directory still holds files
    logger.info("removed %s, its lock, and the empty akar/ directory", STRAY)
    return 0


if __name__ == "__main__":
    sys.exit(main())
