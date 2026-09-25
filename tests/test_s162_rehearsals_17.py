"""s162 w2: the rehearsals re-run fresh -- the reconfirmation record.

On 2026-09-21 this lane re-ran both rehearsal guards fresh from the
repo root (uv run python -m pytest, exit 0):

- tests/test_s130_exhaustion_rehearsal.py, the exhausted verdict
  round-trip: 4 passed
- tests/test_s130_guide_walkthrough.py, the guide's happy path end to
  end: 8 passed

Both guards stood byte-identical to the pins the s139, s144, s148,
s149, s150, s152, s153, s154, s155, s156, s157, s158, s159, s160, and s161 reconfirmation records
carry, so the hashes below carry those versions forward with today's
date. This file is the record, not a re-run: it reads each guard's
bytes and checks the pinned content sha256 against the file as it
stands. When a guard changes on purpose, re-run it fresh and refresh
the pin with a new date. Reads only: no execution, no writes.
"""

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

RECONFIRMATION = {
    "date": "2026-09-21",
    "outcome": "green",
    "guards": {
        "tests/test_s130_exhaustion_rehearsal.py": (
            "af3ead5d99cdc8d3e194af59dbea5794255e8bb4359a3c40fb0f1da2061c3767"
        ),
        "tests/test_s130_guide_walkthrough.py": (
            "a52381f2bdeaad137b8f8e38ddff4ac2dcc0f81b1ee06029c69d2dd69d8923c4"
        ),
    },
}


def test_s162_rehearsal_guards_match_the_reconfirmed_versions() -> None:
    """Each guard stands byte-identical to its reconfirmed version."""
    for rel, pinned in RECONFIRMATION["guards"].items():
        path = REPO / rel
        assert path.is_file(), f"guard missing since {RECONFIRMATION['date']}: {rel}"
        current = hashlib.sha256(path.read_bytes()).hexdigest()
        assert current == pinned, (
            f"{rel} drifted after the {RECONFIRMATION['date']} reconfirmation: "
            f"pinned {pinned[:12]}, now {current[:12]}. Re-run the guard "
            "fresh and refresh the pin with a new date."
        )
