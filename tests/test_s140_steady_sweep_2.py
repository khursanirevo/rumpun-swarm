"""s140 w2: the steady-state sweep record, second iteration.

Ground truth measured 2026-09-21 (solo, repo HEAD 7fa54279ae60):

- the light lanes re-ran green solo: the guide lint (4), the readme
  verbs lint (2), the route-probe serve table (2), plus the two s139
  record files (3): 11 passed, rc 0, /tmp/s140-w2-light.log.
- the rehearsals re-ran green solo: the exhaustion rehearsal (4) and
  the guide walkthrough (8): 12 passed, rc 0, /tmp/s140-w2-rehearsals.log.
- one bounded route probe re-confirmed the serve table: the exact
  glm route shape, --model glm-5.3 (the s139/s125 precedent), one
  call, rc 0, stdout reply `ok`. The stderr carried the known
  catalog warning (CLI-side text, the s125 classification). Trail:
  /tmp/s140-w2-probe.out and /tmp/s140-w2-probe.err.

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
    "tests/test_s139_rehearsals_reconfirm.py":
        "56d413a5adb4a566a05a8d5bc7d1da0532f8130727ba2be446006c9fef7559be",
    "tests/test_s130_exhaustion_rehearsal.py":
        "af3ead5d99cdc8d3e194af59dbea5794255e8bb4359a3c40fb0f1da2061c3767",
    "tests/test_s130_guide_walkthrough.py":
        "a52381f2bdeaad137b8f8e38ddff4ac2dcc0f81b1ee06029c69d2dd69d8923c4",
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
    spec = importlib.util.spec_from_file_location("_s140_s136", S136)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    verdict = module._SERVE_TABLE[PROBE["route"]]
    assert verdict.startswith("serving"), f"the glm verdict drifted: {verdict!r}"
    assert PROBE["model"] in verdict, f"the verdict lost the model: {verdict!r}"
