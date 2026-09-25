"""s277 w2: the rehearsals re-run fresh -- the reconfirmation record.

On 2026-09-24 this lane re-ran both rehearsal guards fresh from the repo
root (uv run python -m pytest, exit 0): 12 passed in 14.00s (the
exhaustion round-trip 4 + the guide walkthrough 8; the walkthrough
dominates the wall time).

Both guards stood byte-identical to the pins s139, s144, s148, s149,
s150, s152, s153, s154, s155, s156, s157, s158, s159, s160, s161, s162,
s163, s164, s165, s166, s167, s168, s169, s170, s171, s172, s173, s174,
s175, s176, s177, s178, s179, s180, s181, s182, s183, s184, s185, s186,
s187, s188, s189, s190, s191, s192, s193, s194, s195, s196, s197, s198,
s199, s200, s201, s202, s203, s204, s205, s206, s207, s208, s209, s210,
s211, s212, s213 records, the s214-labeled record (the s215 and s216 w2
reconfirmations re-landed it), the s217 record
test_s217_rehearsals_72.py, the s218 record test_s218_rehearsals_73.py,
the s219 record test_s219_rehearsals_74.py, the s220 record
test_s220_rehearsals_75.py, the s221 record test_s221_rehearsals_76.py,
the s223 record test_s223_rehearsals_77.py, the s224 record
test_s224_rehearsals_78.py, the s225 record test_s225_rehearsals_79.py,
the s226 record test_s226_rehearsals_80.py, the s227 record
test_s227_rehearsals_81.py, the s228 record test_s228_rehearsals_82.py,
the s229 record test_s229_rehearsals_83.py, the s230 record
test_s230_rehearsals_84.py, the s231 record test_s231_rehearsals_85.py,
the s232 record test_s232_rehearsals_86.py, the s233 record
test_s233_rehearsals_87.py, the s234 record test_s234_rehearsals_88.py,
the s235 record test_s235_rehearsals_89.py, the s236 record
test_s236_rehearsals_90.py, the s237 record test_s237_rehearsals_91.py,
the s238 record test_s238_rehearsals_92.py, the s239 record
test_s239_rehearsals_93.py, the s240 record test_s240_rehearsals_94.py,
the s241 record test_s241_rehearsals_95.py, the s242 record
test_s242_rehearsals_96.py, the s243 record test_s243_rehearsals_97.py,
the s244 record test_s244_rehearsals_98.py, the s245 record
test_s245_rehearsals_99.py, the s246 record test_s246_rehearsals_100.py,
the s247 record test_s247_rehearsals_101.py, the s248 record
test_s248_rehearsals_102.py, the s249 record
test_s249_rehearsals_103.py, the s250 record
test_s250_rehearsals_104.py, the s251 record
test_s251_rehearsals_105.py, the s252 record
test_s252_rehearsals_106.py, the s253 record
test_s253_rehearsals_107.py, the s254 record
test_s254_rehearsals_108.py, the s255 record
test_s255_rehearsals_109.py, the s256 record
test_s256_rehearsals_110.py, the s257 record
test_s257_rehearsals_111.py, the s259 record
test_s259_rehearsals_112.py, the s260 record
test_s260_rehearsals_113.py, the s261 record
test_s261_rehearsals_114.py, the s262 record
test_s262_rehearsals_115.py, the s263 record
test_s263_rehearsals_116.py, the s264 record
test_s264_rehearsals_117.py, the s265 record
test_s265_rehearsals_118.py, the s266 record
test_s266_rehearsals_119.py, the s267 record
test_s267_rehearsals_120.py, the s268 record
test_s268_rehearsals_121.py, the s269 record test_s269_rehearsals_122.py,
the s270 record test_s270_rehearsals_123.py,
the s271 record test_s271_rehearsals_124.py,
the s272 record test_s272_rehearsals_125.py,
the s273 record test_s273_rehearsals_126.py,
the s274 record test_s274_rehearsals_127.py,
the s275 record test_s275_rehearsals_128.py,
the s276 record test_s276_rehearsals_129.py
included, so the hashes below carry those versions forward with today's
date.

The chain carries the s249 token the s251 record dropped and the s252
record restored. This record lands under the next free name, the
convention the s216 w1 lane set with test_s216_light_lanes_71.py. This
file is the record, not a re-run: it reads each guard's bytes and checks
the pinned content sha256 against the file as it stands. When a guard
changes on purpose, re-run it fresh and refresh the pin with a new date.
Reads only: no execution, no writes.
"""

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

RECONFIRMATION = {
    "date": "2026-09-24",
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


def test_s277_rehearsal_guards_match_the_reconfirmed_versions() -> None:
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
