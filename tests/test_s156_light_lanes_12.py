"""s156 w1: the light lanes record, eleventh iteration.

Ground truth measured 2026-09-21 (solo):

- the thirteen guards re-ran green solo: the guide lint (4), the readme
  verbs lint (2), the route-probe serve table (2), the s139 record
  (2), the s140 record (2), the s147 record (2), the s148 record
  (2), the s149 record (2), the s150 record (2), the s152 record (2),
  the s153 record (2), the s154 record (2), the s155 record (2): 28 passed, rc 0,
  /tmp/s156-w1-guards.log.
- one bounded route probe re-confirmed the serve table: the exact
  glm route shape (.rumpun/rumpun.yaml line 38), --model glm-5.3
  (the s125/s132/s139/s140/s145/s146/s147/s148/s149/s150/s152/s153/
  s154/s155 precedent), one call, rc 0, stdout reply `ok`. The stderr carried
  the known catalog warning (CLI-side text, the s125
  classification; 788 bytes, the same shape as the s155 trail).
  Trail: /tmp/s156-w1-probe.out and /tmp/s156-w1-probe.err
  (prompt: /tmp/s156-w1-probe-prompt.txt, rc:
  /tmp/s156-w1-probe.rc).

The record: the guards' versions (sha256 of each guard file's
bytes), the probe result, the sweep date. Reads only: no network,
no writes.

A red on the versions pin means a guard moved since this sweep; the
next steady-state cycle re-runs the guard and refreshes the record.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

SWEEP_DATE = "2026-09-21"

# The guards' versions at the sweep (sha256 of the file bytes).
GUARD_VERSIONS = {
    "tests/test_s136_full_guide_lint.py":
        "208e9054eedc61cc7d590d99caf5fbc50821ccc81d8d793e81d7fbd36a77642e",
    "tests/test_s128_readme_verbs_lint.py":
        "5795fa17b6831697116554833514f41547b42d3642ef1da183c28051b2bc1378",
    "tests/test_s136_route_probes.py":
        "9ecd825b54025199a8f308d7ff5ea580bd31763f96bc71d059b4eb48f4ccef02",
    "tests/test_s139_light_lanes_sweep.py":
        "a329b1d9a30884e986e80ab32d48faac165b806cfec8ce5467909ec76ad13539",
    "tests/test_s140_steady_sweep_2.py":
        "0bae2fc3e78f11ff4ac6c70da6bd0dcffbf0be8c2ea23cf26b2d3b0a74fab26a",
    "tests/test_s147_light_lanes_3.py":
        "9992877f3ecfb6028ca2bffb40ba32f9add4af3ccdad2cf7dda13ce2b5e9cc14",
    "tests/test_s148_light_lanes_4.py":
        "d24a5c5688562be620305dc0b884b5311971535736ace2282b8e898060f54912",
    "tests/test_s149_light_lanes_5.py":
        "fe40794b7d93b152123c33dad44ec3aeccd83298e5a2203574424e3bc0029554",
    "tests/test_s150_light_lanes_6.py":
        "be4bd73a28df1cb74f62087b86d77dfc304b3d05e9e01b6412796ac193595be6",
    "tests/test_s152_light_lanes_8.py":
        "d691c2f7e16ff87a06d44365771c9246a8c47ab68712ef713eeb658f713b1590",
    "tests/test_s153_light_lanes_9.py":
        "9592e9c244ed8328d06cbad3e4ebd0c36546f203ddcf0d4e1701570de7c1b786",
    "tests/test_s154_light_lanes_10.py":
        "70da5afea95c628a4f73f6cf0fa25c17776cfc444ad37ee143a009a4f1b6a9b3",
    "tests/test_s155_light_lanes_11.py":
        "35590aa85b5c2dd9c948c7ebd9b183194fda2e1c4546fbc1e070ce9d95abada2",
}

# The bounded probe result (one call, 2026-09-21).
PROBE = {
    "route": "glm",
    "model": "glm-5.3",
    "rc": 0,
    "reply": "ok",
}

S136 = Path(__file__).resolve().parent / "test_s136_route_probes.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_guard_versions_still_current() -> None:
    """Each recorded guard hash still matches the file's bytes."""
    repo = Path(__file__).resolve().parents[1]
    moved = [
        rel
        for rel, recorded in GUARD_VERSIONS.items()
        if _sha256(repo / rel) != recorded
    ]
    assert not moved, f"guards moved since the {SWEEP_DATE} sweep: {moved}"


def test_serve_table_still_claims_serving() -> None:
    """The s136 serve table's glm verdict still claims serving glm-5.3."""
    spec = importlib.util.spec_from_file_location("_s156_s136", S136)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    verdict = module._SERVE_TABLE[PROBE["route"]]
    assert verdict.startswith("serving"), f"the glm verdict drifted: {verdict!r}"
    assert PROBE["model"] in verdict, f"the verdict lost the model: {verdict!r}"
