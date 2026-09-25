"""s145 w1: the light-lanes sweep record - the record lands.

The s144 w1 lane shipped nothing; this lane is the record re-attempt.

Ground truth measured 2026-09-21 (solo, repo HEAD ab358082bcaa):

- the four guards re-ran green solo: the full-guide lint (4 tests),
  the readme verbs lint (2), the route-probe serve table (2), and the
  s139 sweep record itself (2); 10 passed, rc 0 each. Logs:
  /tmp/s145-w1-{guide,readme,probes,sweep}.log.
- one bounded route probe re-confirmed the serve table: the exact glm
  route shape with --model glm-5.3 (the s125/s132 precedent), one call,
  rc 0, stdout reply `ok`. The stderr carried the known catalog warning
  (`glm-5.3` isn't described by this version's model catalog), the
  CLI-side text the s125 notes classified as not a serving error.
  Probe trail: /tmp/s145-w1-probe.out and /tmp/s145-w1-probe.err.

Re-confirmed 2026-09-21 by the s146 w1 lane (solo, repo HEAD
9d46c0a): the four guards re-ran green solo (10 passed, rc 0;
logs /tmp/s146-w1-{guide,readme,probes,sweep}.log) and the bounded
glm-5.3 probe re-served (rc 0, reply `ok`). One drift named: the
stdout carried `ok` plus a stray idle move-block addendum (31
bytes; trail /tmp/s146-w1-probe.out); the stderr carried the same
known catalog warning (788 bytes, matching the s145 trail). Zero
pin drift: all four recorded guard hashes still match.

The record: the guards' versions (sha256 of each guard file's bytes),
the probe result, the sweep date. Reads only: no network, no writes;
the real campaign files are read-only here.

A red on the versions pin means a guard moved since this sweep; the
next steady-state cycle re-runs the guard and refreshes the record.

The s139 file (tests/test_s139_light_lanes_sweep.py) joined the guard
set after its own sweep, so this record's versions cover four files.
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
    spec = importlib.util.spec_from_file_location("_s145_s136", S136)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    verdict = module._SERVE_TABLE[PROBE["route"]]
    assert verdict.startswith("serving"), f"the glm verdict drifted: {verdict!r}"
    assert PROBE["model"] in verdict, f"the verdict lost the model: {verdict!r}"
