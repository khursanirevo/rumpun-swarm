"""H6 old-code window loop (s18 w1): how often both same-id appends succeed.

Runs the s17 draft's barrier scenario 20 times against the UNPATCHED repo
akar. Both-appends-succeed is the review's silent-replacement signature;
exactly-one-succeeds means the scheduler did not interleave the two threads
inside the unserialised check-then-publish window (the pin then passes for
lack of the race, not for its absence). Run:

    .venv/bin/python .rumpun/rimba/s18/w1/h6_oldcode_loop.py
"""

import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, "/mnt/data/work/rumpun/src")  # unpatched repo tree

from rumpun import akar  # noqa: E402


def _attempt(root: Path, barrier: threading.Barrier, k: int, outcomes: list) -> None:
    barrier.wait()
    try:
        akar.append_record(root, "race-loop", f"t{k}", f"body {k}")
        outcomes.append("ok")
    except akar.AkarError:
        outcomes.append("err")


def main() -> int:
    runs = 20
    both = 0
    for _ in range(runs):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            outcomes: list[str] = []
            barrier = threading.Barrier(2)
            threads = [
                threading.Thread(target=_attempt, args=(root, barrier, k, outcomes))
                for k in (0, 1)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(10)
            if sorted(outcomes) == ["ok", "ok"]:
                both += 1
    print(f"unpatched akar: both-appends-succeeded in {both} of {runs} barrier runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
