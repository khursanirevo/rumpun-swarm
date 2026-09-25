"""s88 w2 pins — the standing usefulness assessment, sealed every close.

Spec source: the sealed precedent .rumpun/ledger/2026-09-17_usefulness-s87.md
(read first; it is the spec) and the s88 w2 brief
(.rumpun/runs/s88/w2/prompt.md). s87 answered the stopping question with
fronts, not vibes; these pins hold the contract that makes it permanent:
every close seals one usefulness-<sid> record, the verdict vocabulary is
CONTINUE | PAUSE | EXHAUSTED, and every front names its owner and
next-action.

Contract these pins hold -- src/rumpun/audit.py
(seal_usefulness_assessment / usefulness_inputs / read_usefulness_assessment),
wired through `rumpun harvest <sid> --assessment-file <yaml>`:

1. Composition is byte-stable: fronts in, the s87 body shape out -- the
   verdict line, the basis line (the default pinned verbatim), the fronts
   each rendered `- <name> - owner: <owner>. <basis> Next: <next>.`, the
   satisfied header, one bullet per satisfied line; the sealed sha256
   digests exactly those body bytes.
2. The verdict vocabulary is enforced: an unknown verdict refuses with
   ValueError naming the vocabulary; lowercase is not a verdict; PAUSE and
   EXHAUSTED seal, and EXHAUSTED with zero fronts keeps every section
   header, so the shape is byte-stable at every arity.
3. The s87 precedent parses: the committed record reads back through
   read_usefulness_assessment -- digest intact, verdict CONTINUE, eight
   fronts each named with an owner, the two no-Next fronts reading next ""
   (the reader is lenient where the precedent is; the composer never emits
   that shape).
4. Round-trip: what the composer seals, the reader reads back
   field-identical.
5. Front shapes refuse: a front without owner or next is an AuditError,
   never a silent skip; an owner carrying ". " and a basis carrying
   " Next: " refuse (they would not read back).
6. CLI wiring: `rumpun harvest <sid> --assessment-file` seals
   usefulness-<sid> beside the harvest record in one close (harvest
   record, verdict row, and assessment all land).
7. CLI refusal is pre-flight and whole: a bad assessment file refuses the
   close before anything lands -- no harvest record, no verdict row, no
   assessment -- and the refusal names the vocabulary on stderr.

Offline: every pin is in-process or a bounded subprocess over tmp_path
fixture campaigns (the s57w2 layout: terminal state.json, .rumpun/
rumpun.yaml, a fixture-local ledger). No route call, no gh call, no
network; the only file read outside tmp is the committed s87 record.

Grafting: drop this file into tests/. Helpers and constants carry the
_s88w2_ prefix; nothing collides with existing defs.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from rumpun import audit as audit_mod

_S88W2_TIMEOUT = 240
_S88W2_S87 = Path(".rumpun") / "ledger" / "2026-09-17_usefulness-s87.md"
_S88W2_DEFAULT_BASIS = (
    "directive seq 9 - usefulness exhaustion is the stopping criterion;"
    " every front below names its owner and next-action"
)

_S88W2_STATE = {
    "id": "SET_BY_BUILDER",
    "status": "completed",
    "started_at": 1789000000.0,
    "ended_at": 1789000005.0,
    "stall_s": 2700.0,
    "agents": {
        "w1": {
            "name": "w1",
            "route": "fable",
            "state": "exited",
            "exit_code": 0,
            "seconds": 5.0,
        }
    },
}

_S88W2_FRONTS = [
    {
        "name": "issue #13 retirement",
        "owner": "campaign (s88 w1, in flight)",
        "basis": "the suite gate fix landed in s86; the board issue itself is not closed.",
        "next": "w1 comments the s86 evidence onto the issue and closes it",
    },
    {
        "name": "issues #11 and #12, the route credits",
        "owner": "operator",
        "basis": "the panel sweep windows wait behind the credits.",
        "next": "the operator refills the credits",
    },
]
_S88W2_SATISFIED = ["the board hygiene arc - #10 retired on the sealed s83 evidence"]

_S88W2_YAML = """\
verdict: CONTINUE
basis: pin basis from the file
fronts:
- name: issue #13 retirement
  owner: campaign (s88 w1, in flight)
  basis: the suite gate fix landed in s86
  next: w1 comments the evidence and closes it
- name: issues #11 and #12, the route credits
  owner: operator
  basis: the sweep windows wait behind the credits
  next: the operator refills the credits
satisfied:
- "the board hygiene arc - #10 retired on the sealed s83 evidence"
"""


def _s88w2_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml."""
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise AssertionError("no pyproject.toml above the pins file")


def _s88w2_env() -> dict[str, str]:
    """Subprocess env with the repo src/ first on PYTHONPATH."""
    env = dict(os.environ)
    src = str(_s88w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s88w2_run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """One bounded subprocess run; a timeout is a pin failure, not a hang."""
    try:
        return subprocess.run(
            argv, cwd=str(cwd), env=_s88w2_env(), capture_output=True,
            text=True, timeout=_S88W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"{' '.join(argv[1:4])} exceeded {_S88W2_TIMEOUT}s"
        raise AssertionError(msg) from exc


def _s88w2_campaign(tmp_path: Path, sid: str) -> Path:
    """A fixture campaign: terminal state.json, rumpun.yaml, empty ledger."""
    campaign = tmp_path / "s88w2proj"
    root = campaign / ".rumpun"
    (root / "runs" / sid / "_season").mkdir(parents=True)
    (root / "seasons").mkdir()
    (root / "ledger").mkdir()
    (root / "rumpun.yaml").write_text("campaign: fixture\n", encoding="utf-8")
    state = dict(_S88W2_STATE, id=sid)
    (root / "runs" / sid / "_season" / "state.json").write_text(
        json.dumps(state, indent=2) + "\n", encoding="utf-8",
    )
    (root / "seasons" / f"{sid}.yaml").write_text(
        "goal: pin the standing usefulness assessment\n", encoding="utf-8",
    )
    return campaign


def _s88w2_record_path(ledger: Path, marker: str) -> Path:
    """The ledger file carrying `marker` (e.g. 'id: usefulness-s88fx')."""
    for path in sorted(ledger.iterdir()):
        if path.is_file() and marker in path.read_text(encoding="utf-8", errors="replace"):
            return path
    listing = sorted(p.name for p in ledger.iterdir()) if ledger.is_dir() else []
    body = "\n".join(listing) or "(no ledger)"
    msg = f"no record carrying {marker!r} in {ledger}:\n{body}"
    raise AssertionError(msg)


def test_s88w2_composition_is_byte_stable(tmp_path: Path) -> None:
    """Fronts in, the s87 body shape out, byte for byte; sha digests the body."""
    root = tmp_path / "s88w2ledger"
    path = audit_mod.seal_usefulness_assessment(
        root, "s88fx", "CONTINUE", _S88W2_FRONTS, satisfied=_S88W2_SATISFIED,
    )
    lines = path.read_text(encoding="utf-8").splitlines()
    front_one = (
        "- issue #13 retirement - owner: campaign (s88 w1, in flight)."
        " the suite gate fix landed in s86; the board issue itself is not closed."
        " Next: w1 comments the s86 evidence onto the issue and closes it."
    )
    front_two = (
        "- issues #11 and #12, the route credits - owner: operator."
        " the panel sweep windows wait behind the credits."
        " Next: the operator refills the credits."
    )
    expected_body = "\n".join(
        [
            "verdict: CONTINUE",
            f"basis: {_S88W2_DEFAULT_BASIS}",
            "fronts:",
            front_one,
            front_two,
            "satisfied (recorded, not fronts):",
            "- the board hygiene arc - #10 retired on the sealed s83 evidence",
        ]
    )
    assert "\n".join(lines[4:-1]) == expected_body
    assert lines[1] == "id: usefulness-s88fx"
    assert lines[3] == (
        "title: CONTINUE (the per-season usefulness assessment over the whole ledger)"
    )
    assert lines[-1] == f"sha256: {hashlib.sha256(expected_body.encode('utf-8')).hexdigest()}"


def test_s88w2_unknown_verdict_refuses(tmp_path: Path) -> None:
    """The vocabulary is CONTINUE | PAUSE | EXHAUSTED; anything else refuses."""
    root = tmp_path / "s88w2ledger"
    with pytest.raises(ValueError, match="CONTINUE\\|PAUSE\\|EXHAUSTED"):
        audit_mod.seal_usefulness_assessment(root, "s88fx", "MAYBE", _S88W2_FRONTS)
    with pytest.raises(ValueError, match="CONTINUE\\|PAUSE\\|EXHAUSTED"):
        audit_mod.seal_usefulness_assessment(root, "s88fx", "continue", _S88W2_FRONTS)
    assert not (root / "ledger").exists() or not any((root / "ledger").iterdir())


def test_s88w2_pause_and_exhausted_seal(tmp_path: Path) -> None:
    """PAUSE seals; EXHAUSTED seals with zero fronts, headers still in place."""
    pause_root = tmp_path / "s88w2pause"
    path = audit_mod.seal_usefulness_assessment(pause_root, "s88fx", "PAUSE", _S88W2_FRONTS)
    assert "verdict: PAUSE" in path.read_text(encoding="utf-8")
    exhausted_root = tmp_path / "s88w2exhausted"
    path = audit_mod.seal_usefulness_assessment(exhausted_root, "s88fy", "EXHAUSTED", [])
    body = "\n".join(path.read_text(encoding="utf-8").splitlines()[4:-1])
    assert body == (
        "verdict: EXHAUSTED\n"
        f"basis: {_S88W2_DEFAULT_BASIS}\n"
        "fronts:\n"
        "satisfied (recorded, not fronts):"
    )


def test_s88w2_s87_precedent_parses() -> None:
    """The sealed s87 record is the spec: it reads back whole, digest intact."""
    record = _s88w2_repo() / _S88W2_S87
    assert record.is_file(), f"the sealed s87 precedent is missing: {record}"
    data = audit_mod.read_usefulness_assessment(record)
    assert data["id"] == "usefulness-s87"
    assert data["verdict"] == "CONTINUE"
    assert len(data["fronts"]) == 8
    for front in data["fronts"]:
        assert front["name"] and front["owner"]
    assert data["fronts"][0]["name"] == "issue #13 retirement"
    assert data["fronts"][0]["owner"] == "campaign (s87 w1, in flight)"
    assert data["fronts"][0]["next"].startswith("w1 comments the s86 evidence")
    assert data["fronts"][5]["next"] == ""  # the competition arc: no Next: segment
    assert data["fronts"][6]["name"] == "issue #5"
    assert len(data["satisfied"]) == 3
    assert "seq 9" in data["basis"]
    assert "usefulness" in data["title"]


def test_s88w2_round_trip_is_field_identical(tmp_path: Path) -> None:
    """What the composer seals, the reader reads back field-identical."""
    root = tmp_path / "s88w2ledger"
    path = audit_mod.seal_usefulness_assessment(
        root, "s88fx", "CONTINUE", _S88W2_FRONTS,
        satisfied=_S88W2_SATISFIED, basis="round trip basis",
    )
    data = audit_mod.read_usefulness_assessment(path)
    assert data["verdict"] == "CONTINUE"
    assert data["basis"] == "round trip basis"
    assert data["fronts"] == _S88W2_FRONTS
    assert data["satisfied"] == _S88W2_SATISFIED


def test_s88w2_front_shapes_refuse(tmp_path: Path) -> None:
    """A front without owner or next refuses; separators that would not
    read back refuse; never a silent skip."""
    root = tmp_path / "s88w2ledger"
    with pytest.raises(audit_mod.AuditError, match="owner"):
        audit_mod.seal_usefulness_assessment(
            root, "s88fx", "CONTINUE", [{"name": "n", "next": "x"}],
        )
    with pytest.raises(audit_mod.AuditError, match="next"):
        audit_mod.seal_usefulness_assessment(
            root, "s88fx", "CONTINUE", [{"name": "n", "owner": "o"}],
        )
    with pytest.raises(audit_mod.AuditError, match="owner"):
        audit_mod.seal_usefulness_assessment(
            root, "s88fx", "CONTINUE",
            [{"name": "n", "owner": "o. x", "next": "x"}],
        )
    with pytest.raises(audit_mod.AuditError, match="next separator"):
        audit_mod.seal_usefulness_assessment(
            root, "s88fx", "CONTINUE",
            [{"name": "n", "owner": "o", "basis": "b Next: t", "next": "x"}],
        )


def test_s88w2_harvest_seals_the_assessment(tmp_path: Path) -> None:
    """The harvest verb seals usefulness-<sid> beside the harvest record."""
    campaign = _s88w2_campaign(tmp_path, "s88fx")
    (campaign / "assessment.yaml").write_text(_S88W2_YAML, encoding="utf-8")
    proc = _s88w2_run(
        campaign,
        [sys.executable, "-m", "rumpun", "harvest", "s88fx",
         "--verdict", "WIN", "--implies", "fixture close for the standing assessment",
         "--assessment-file", "assessment.yaml"],
    )
    assert proc.returncode == 0, f"rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"
    ledger = campaign / ".rumpun" / "ledger"
    assessment = _s88w2_record_path(ledger, "id: usefulness-s88fx")
    _s88w2_record_path(ledger, "id: s88fx-harvest")
    data = audit_mod.read_usefulness_assessment(assessment)
    assert data["verdict"] == "CONTINUE"
    assert data["basis"] == "pin basis from the file"
    assert len(data["fronts"]) == 2
    assert data["satisfied"] == _S88W2_SATISFIED
    assert (campaign / ".rumpun" / "runs" / "s88fx" / "verdicts.jsonl").is_file()


def test_s88w2_bad_assessment_refuses_the_whole_close(tmp_path: Path) -> None:
    """A bad assessment file refuses pre-flight: nothing lands, the refusal
    names the vocabulary, and the harvest itself does not happen."""
    campaign = _s88w2_campaign(tmp_path, "s88fy")
    (campaign / "assessment.yaml").write_text("verdict: MAYBE\nfronts: []\n", encoding="utf-8")
    proc = _s88w2_run(
        campaign,
        [sys.executable, "-m", "rumpun", "harvest", "s88fy",
         "--verdict", "WIN", "--implies", "fixture close for the standing assessment",
         "--assessment-file", "assessment.yaml"],
    )
    assert proc.returncode != 0, f"the close should refuse:\n{proc.stdout}\n{proc.stderr}"
    assert "must be one of CONTINUE|PAUSE|EXHAUSTED" in proc.stderr
    ledger = campaign / ".rumpun" / "ledger"
    assert ledger.is_dir() and not any(ledger.iterdir())
    assert not (campaign / ".rumpun" / "runs" / "s88fy" / "verdicts.jsonl").exists()
