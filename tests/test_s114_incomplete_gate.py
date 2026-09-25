"""s114 w2 pins - the harvest gate: the record says what the notes gate saw.

Spec source: the s114 w2 brief. The s112 gate marks a notes-less exit on
the state snap and the results row (the s113 w2 row is the live exemplar:
state "exited", exit_code 0, incomplete "notes.md missing"); the harvest
record still read clean. The record should say what the gate saw.

The gate: _render_body gains one line per agent whose persisted snap
carries the additive incomplete key -- "incomplete <unit>: <value>", the
value verbatim -- placed with the harness-observed facts ([H] per P36),
before the caller-supplied verdict lines. A clean season's body gains
nothing: byte-identical shape, pinned exactly.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 on the pre-gate tree, pins 1 and 3
  (the record carried no incomplete line); /tmp/s114-w2-pins-red.txt.
- GREEN captured 2026-09-20 post-gate; /tmp/s114-w2-pins-green.txt.
- Pin 2 is green on both sides by design: it pins the clean clause
  byte-for-byte, so a later regression cannot dress a clean season with
  the mark.

Bounds honored: fixtures hand-built in tmp_path (harvest_season takes the
tmp root, so the real ledger is never touched -- the CLI harvest verb
never runs in tests); nothing copied from live .rumpun/runs state;
offline, seconds-fast.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rumpun import harvest


def _s114w2_state(root: Path, sid: str, agents: dict[str, dict[str, Any]]) -> None:
    """Completed season state, as engine._finalize would leave it."""
    state_dir = root / "runs" / sid / "_season"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text(
        json.dumps(
            {
                "id": sid,
                "status": "completed",
                "started_at": 1.0,
                "ended_at": 2.0,
                "agents": agents,
            }
        ),
        encoding="utf-8",
    )


def _s114w2_clean(name: str) -> dict[str, Any]:
    """One exited-0 writer snap with notes.md present (no gate key)."""
    return {
        "name": name,
        "route": "glm",
        "state": "exited",
        "exit_code": 0,
        "seconds": 1.0,
    }


def _s114w2_marked(name: str) -> dict[str, Any]:
    """The s113 w2 live exemplar's shape: exited 0, the gate key set."""
    return {
        "name": name,
        "route": "fable",
        "state": "exited",
        "exit_code": 0,
        "seconds": 1.0,
        "incomplete": "notes.md missing",
    }


def _s114w2_record_body(path: Path) -> str:
    """The record body per akar.append_record's recovery contract."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[4:-1])


# pin 1 - the gate at the record layer: a harvest over a season whose
# results rows carry the incomplete key appends the incomplete line to
# the record body (unit, the key's value), with the [H] facts and before
# the caller-supplied verdict lines. Only the marked unit is named.
def test_s114w2_harvest_record_carries_incomplete_line(tmp_path: Path) -> None:
    _s114w2_state(
        tmp_path, "s1", {"w1": _s114w2_clean("w1"), "w2": _s114w2_marked("w2")}
    )
    path = harvest.harvest_season(tmp_path, "s1", "WIN", "note")
    body = _s114w2_record_body(path)
    assert "incomplete w2: notes.md missing" in body
    assert "incomplete w1" not in body
    assert body.index("incomplete w2:") < body.index("verdict: WIN")


# pin 2 - the clean clause (green on both sides by design): a clean
# season's record stays byte-identical in shape; the pinned body is the
# exact pre-gate rendering.
def test_s114w2_clean_record_byte_identical(tmp_path: Path) -> None:
    _s114w2_state(tmp_path, "s1", {"w1": _s114w2_clean("w1")})
    path = harvest.harvest_season(tmp_path, "s1", "WIN", "note")
    expected = (
        "season s1: completed\n"
        "duration: 1s\n"
        "\n"
        "| agent | route | state | exit_code | seconds |\n"
        "|---|---|---|---|---|\n"
        "| w1 | glm | exited | 0 | 1.0 |\n"
        "\n"
        "spend: writers=1 writer_seconds=1.0 duration_s=1\n"
        "\n"
        "verdict: WIN\n"
        "implies: note"
    )
    assert _s114w2_record_body(path) == expected


# pin 3 - the key's value passes through verbatim, one line per marked
# unit, sorted; the gate never rewrites a gap it did not observe.
def test_s114w2_value_verbatim_one_line_per_unit(tmp_path: Path) -> None:
    a1 = dict(_s114w2_marked("a1"), incomplete="notes.md still missing")
    _s114w2_state(
        tmp_path, "s1", {"b2": _s114w2_marked("b2"), "a1": a1}
    )
    path = harvest.harvest_season(tmp_path, "s1", "NEUTRAL", "note")
    body = _s114w2_record_body(path)
    marked = [ln for ln in body.splitlines() if ln.startswith("incomplete ")]
    assert marked == [
        "incomplete a1: notes.md still missing",
        "incomplete b2: notes.md missing",
    ]
