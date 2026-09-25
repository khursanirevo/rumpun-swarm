"""s57 w2 pins — the check rides every close, pinned before it exists.

Spec-first pins (red against current code) for the s57 contract (season
goal seasons/s57.yaml: "the verdict row and the check record land
together, so a season's WIN never rests only on its own workers'
reports"; w1's brief .rumpun/prompts/dev/w1-harvest-check.md; ledger
anchors 2026-09-16_s56-harvest and 2026-09-16_audit-39/40, the
usefulness residual the ride-along check closes). Spec anchors, the
interface contract, and the measured red set: .rumpun/runs/s57/w2/notes.md.

Interface these pins hold (w1's brief): `rumpun harvest <sid> --verdict V
--implies X` runs the artifact check (the cmd_check path: the checker at
<project-root>/tools/artifact_check.py as an isolated subprocess, sid and
the repo HEAD) AFTER writing the verdict row; the check-<sid> record lands
in the default ledger dir beside the <sid>-harvest record. A check DELTA
or structural refusal never suppresses or rewrites the verdict; the exit
code reflects the harvest (not the check) unless --strict. cwd inside the
fixture project resolves it (the verb walks up to .rumpun/rumpun.yaml).

Every pin builds a check-compatible fixture campaign (a miniature repo:
DESIGN.md with a true ships row, src/rumpun/__init__.py, committed pins
that pass in the extracted tree, tools/artifact_check.py, .rumpun/ tree,
a terminal state.json with fixed timestamps) and drives harvest as a
subprocess bounded by S57W2_TIMEOUT (the spec's 240s bound). No pin
writes the real ledger: everything lives under pytest tmp_path.

Red against current main (cli.py cmd_harvest appends the record and row
and runs no check; --strict is unknown): pins 1, 2, 3a red at HEAD for
the spec reason (no check rides the close, so no check record, no DELTA
beside the verdict, no refusal to surface); pin 3b is green at HEAD and
guards the merge: the harvest record must stay byte-stable once the
check rides along. Green at merge via w1's wiring. Grafting: land this
file in tests/ as-is (additions-only; existing suite files stay
untouched). Helpers carry the _s57w2_ prefix, so nothing collides with
existing defs. No rumpun imports: subprocess and file reads only.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

S57W2_TIMEOUT = 240  # the spec bound for one harvest run
S57W2_IMPLIES = "fixture close: the check rides the harvest"
S57W2_STATE = {
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

FX_PINS_BODY = '''\
"""Fixture pins: two passing checks, no rumpun import needed."""


def test_fx_sanity_math() -> None:
    assert 1 + 1 == 2


def test_fx_sanity_text() -> None:
    assert "fx".upper() == "FX"
'''


def _s57w2_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and
    grafted into tests/ (post-graft): both sit under the repo root.
    """
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise AssertionError("no pyproject.toml above the pins file")


def _s57w2_env() -> dict[str, str]:
    """The subprocess env: repo src/ on PYTHONPATH ahead of any inherited value."""
    env = dict(os.environ)
    src = str(_s57w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s57w2_run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """One bounded subprocess run; a timeout is a pin failure, not a hang."""
    try:
        return subprocess.run(
            argv, cwd=str(cwd), env=_s57w2_env(), capture_output=True,
            text=True, timeout=S57W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"{' '.join(argv[1:4])} exceeded {S57W2_TIMEOUT}s"
        raise AssertionError(msg) from exc


def _s57w2_git(root: Path, *argv: str) -> str:
    """One local git command in the fixture; nonzero is a build error."""
    proc = subprocess.run(
        ["git", "-C", str(root), *argv], capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"git {' '.join(argv)}: {proc.stdout}{proc.stderr}"
    return proc.stdout


def _s57w2_design(sid: str, ships: str | None) -> str:
    """The fixture DESIGN.md: a ships table with the season's row (or none)."""
    head = (
        "# Fixture design\n\n"
        "A minimal check-compatible campaign used by the s57 w2 pins.\n\n"
        "| season | outcome | ships |\n"
        "|---|---|---|\n"
    )
    if ships is None:
        return head
    return head + f"| {sid} | WIN | {ships} |\n"


def _s57w2_fixture(root: Path, sid: str, ships: str | None) -> Path:
    """Build a check-compatible fixture campaign at root and commit it.

    The ships row is check-compatible: the claimed file exists, no key,
    slash, pins, or suite claims. state.json pins timestamps and the agent
    table so the harvest record is byte-deterministic (pin 3b).
    """
    rumpun_dir = root / ".rumpun"
    (rumpun_dir / "runs" / sid / "_season").mkdir(parents=True)
    (root / "src" / "rumpun").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "tools").mkdir()
    (rumpun_dir / "rumpun.yaml").write_text(
        "campaign: fixture\n", encoding="utf-8",
    )
    (root / "DESIGN.md").write_text(_s57w2_design(sid, ships), encoding="utf-8")
    (root / "src" / "rumpun" / "__init__.py").write_text(
        '__version__ = "0.0.0-fixture"\n', encoding="utf-8",
    )
    (root / "tests" / f"test_{sid}_sanity.py").write_text(
        FX_PINS_BODY, encoding="utf-8",
    )
    checker = _s57w2_repo() / "tools" / "artifact_check.py"
    (root / "tools" / "artifact_check.py").write_bytes(checker.read_bytes())
    state = dict(S57W2_STATE, id=sid)
    (rumpun_dir / "runs" / sid / "_season" / "state.json").write_text(
        json.dumps(state, indent=2) + "\n", encoding="utf-8",
    )
    _s57w2_git(root, "init", "-q")
    _s57w2_git(root, "add", "-A")
    _s57w2_git(root, "-c", "user.name=fx", "-c", "user.email=fx@example.com",
               "commit", "-qm", "fixture season")
    listed = _s57w2_git(root, "ls-files")
    for needed in (
        "DESIGN.md", ".rumpun/rumpun.yaml", "src/rumpun/__init__.py",
        f"tests/test_{sid}_sanity.py", "tools/artifact_check.py",
    ):
        assert needed in listed.splitlines(), f"fixture commit lost {needed}"
    return root


def _s57w2_harvest(root: Path, sid: str, *extra: str) -> subprocess.CompletedProcess[str]:
    """One bounded `rumpun harvest <sid> --verdict WIN --implies ...` run."""
    argv = [
        sys.executable, "-m", "rumpun", "harvest", sid,
        "--verdict", "WIN", "--implies", S57W2_IMPLIES, *extra,
    ]
    return _s57w2_run(root, argv)


def _s57w2_ledger(root: Path) -> Path:
    return root / ".rumpun" / "ledger"


def _s57w2_record(ledger: Path, marker: str) -> str:
    """The ledger record carrying `marker` (e.g. 'id: check-<sid>')."""
    if not ledger.is_dir():
        msg = f"ledger dir missing (nothing was written): {ledger}"
        raise AssertionError(msg)
    hits: list[str] = []
    for path in sorted(ledger.iterdir()):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            if marker in text:
                hits.append(text)
    if not hits:
        listing = "\n".join(sorted(p.name for p in ledger.iterdir()))
        msg = f"no record carrying {marker!r} in {ledger}:\n{listing}"
        raise AssertionError(msg)
    return hits[0]


def _s57w2_record_verdict(record: str) -> str:
    """The verdict token of the record's `verdict:` line."""
    found = re.search(r"^verdict: (\S+)", record, re.M)
    assert found is not None, f"record carries no verdict line:\n{record}"
    return found.group(1)


def _s57w2_row(root: Path, sid: str) -> dict[str, str]:
    """The single season verdict row from the run tree, parsed."""
    path = root / ".rumpun" / "runs" / sid / "verdicts.jsonl"
    assert path.is_file(), f"verdict row missing: {path}"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1, f"expected exactly one verdict row, got {len(lines)}: {lines}"
    row = json.loads(lines[0])
    assert row["season"] == sid, row
    return row


# --- spec 1: the close lands both records ------------------------------------


def test_s57w2_harvest_lands_row_and_check_record(tmp_path: Path) -> None:
    """`rumpun harvest fx01` lands the verdict row AND the check-fx01 record.

    The honest fixture closes: exit 0; the verdicts row carries the
    operator's WIN; the <sid>-harvest record sits in the ledger; and the
    check-fx01 record rides along in the same ledger dir with verdict
    VERIFIED and no DELTA (the fixture's ships row is true, so the check
    verifies).
    """
    root = _s57w2_fixture(tmp_path / "fx", "fx01", "tests/test_fx01_sanity.py exists")
    proc = _s57w2_harvest(root, "fx01")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    row = _s57w2_row(root, "fx01")
    assert row["verdict"] == "WIN", row
    harvest_record = _s57w2_record(_s57w2_ledger(root), "id: fx01-harvest")
    assert _s57w2_record_verdict(harvest_record) == "WIN", harvest_record
    check_record = _s57w2_record(_s57w2_ledger(root), "id: check-fx01")
    assert _s57w2_record_verdict(check_record) == "VERIFIED", check_record
    assert "DELTA" not in check_record, check_record


# --- spec 2: a DELTA is recorded beside the verdict, never suppressed --------


def test_s57w2_delta_check_does_not_rewrite_the_verdict(tmp_path: Path) -> None:
    """A tampered ships row yields DELTA; the verdict row stands untouched.

    The fixture closes honestly, then the ships row is tampered to claim a
    file the tree lacks and committed (HEAD = the tampered tree). The
    harvest still lands the verdict row and the harvest record with the
    operator's WIN, and the check-fx03 record carries DELTA beside them:
    recorded, not suppressed, never rewritten into the verdict. Exit 0
    reflects the harvest, not the check (w1's brief honesty clause).
    """
    root = _s57w2_fixture(tmp_path / "fx", "fx03", "tests/test_fx03_sanity.py exists")
    design = root / "DESIGN.md"
    design.write_text(
        design.read_text(encoding="utf-8").replace(
            "tests/test_fx03_sanity.py exists",
            "tests/test_fx03_missing.py exists, tests/test_fx03_sanity.py exists",
        ),
        encoding="utf-8",
    )
    _s57w2_git(root, "-c", "user.name=fx", "-c", "user.email=fx@example.com",
               "commit", "-qam", "tamper: the ships row claims a missing file")
    proc = _s57w2_harvest(root, "fx03")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    row = _s57w2_row(root, "fx03")
    assert row["verdict"] == "WIN", row
    harvest_record = _s57w2_record(_s57w2_ledger(root), "id: fx03-harvest")
    assert _s57w2_record_verdict(harvest_record) == "WIN", harvest_record
    check_record = _s57w2_record(_s57w2_ledger(root), "id: check-fx03")
    assert _s57w2_record_verdict(check_record) == "DELTA", check_record


# --- spec 3: the refusal surfaces; the record stays byte-stable --------------


def test_s57w2_structural_refusal_exits_nonzero(tmp_path: Path) -> None:
    """A season with no ships row: the check refuses; --strict exits nonzero.

    fx02 has a terminal state but no row in the fixture DESIGN.md, so the
    ride-along check's structural refusal (unknown season id) is the only
    honest outcome; under --strict the harvest must exit nonzero and the
    streams name what is missing (the sid). Red today for the spec reason:
    the close runs no check, so nothing refuses -- the harvest just
    succeeds.
    """
    root = _s57w2_fixture(tmp_path / "fx", "fx02", None)
    proc = _s57w2_harvest(root, "fx02", "--strict")
    streams = proc.stdout + proc.stderr
    assert proc.returncode != 0, streams
    assert "fx02" in streams, f"refusal must name the missing sid:\n{streams}"


def test_s57w2_harvest_record_byte_stable_across_runs(tmp_path: Path) -> None:
    """Two closes of the honest fixture produce byte-identical harvest records.

    The fixture pins every input of the record (fixed timestamps, fixed
    agent table, same verdict/implies), so two independent fixture copies
    must append byte-equal <sid>-harvest files. Guards the merge: the
    ride-along check must not smuggle clocks or check output into the
    harvest record. Red basis note: green at HEAD (today's record is
    already deterministic) -- this pin holds the merge, not the red set.
    """
    first = _s57w2_fixture(tmp_path / "one", "fx01", "tests/test_fx01_sanity.py exists")
    second = _s57w2_fixture(tmp_path / "two", "fx01", "tests/test_fx01_sanity.py exists")
    first_proc = _s57w2_harvest(first, "fx01")
    assert first_proc.returncode == 0, first_proc.stdout + first_proc.stderr
    second_proc = _s57w2_harvest(second, "fx01")
    assert second_proc.returncode == 0, second_proc.stdout + second_proc.stderr
    one = _s57w2_record(_s57w2_ledger(first), "id: fx01-harvest")
    two = _s57w2_record(_s57w2_ledger(second), "id: fx01-harvest")
    assert one.encode("utf-8") == two.encode("utf-8"), (
        f"harvest record is not byte-stable:\n--- run one ---\n{one}\n"
        f"--- run two ---\n{two}"
    )
