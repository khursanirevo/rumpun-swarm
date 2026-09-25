"""s115 w2 pins — the close check names the missing design convention.

Spec-first pins (red against current code) for the s115 w2 contract
(issues #36 and #37: a campaign repo whose extract carries no
DESIGN.md convention makes the harvest close check refuse exit 2,
indistinguishable from tamper; measured red set:
.rumpun/runs/s115/w2/notes.md).

The contract these pins hold: tools/artifact_check.py, when the
extracted tree carries no DESIGN.md, must not take the structural
refusal. With no pins lane either, nothing is checkable: the named
skip line naming the convention, exit 0, no record (the s108
pinless-skip shape). With a pins lane, the SHIPS phase skips, the
record carries the note, and pins, pack digests, and seals still
bind. A DESIGN.md present but missing the season's row keeps today's
exit 2 (the tamper-sensitive case). A repo WITH the convention is
byte-unchanged. Grafting: land this file in tests/ as-is
(additions-only; existing suite files stay untouched). Helpers carry
the _s115nd_ prefix, so nothing collides with existing defs. No
rumpun imports: subprocess and file reads only.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

S115ND_TIMEOUT = 240  # the checker's own pins bound; a timeout is a pin failure

FX_PINS_BODY = '''\
"""Fixture pins: two passing checks, no rumpun import needed."""


def test_fx_sanity_math() -> None:
    assert 1 + 1 == 2


def test_fx_sanity_text() -> None:
    assert "fx".upper() == "FX"
'''


def _s115nd_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically pre-graft (the w2 workspace) and post-graft
    (tests/): both sit under the repo root.
    """
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise AssertionError("no pyproject.toml above the pins file")


def _s115nd_env() -> dict[str, str]:
    """The subprocess env: repo src/ on PYTHONPATH ahead of any inherited value."""
    env = dict(os.environ)
    src = str(_s115nd_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s115nd_run(
    root: Path, sid: str, out_dir: Path,
) -> subprocess.CompletedProcess[str]:
    """One bounded checker subprocess run: sid @ HEAD, record into out_dir.

    The fixture's own checker copy runs, not the repo's: the checker
    resolves the repo from its own file location, so the repo's copy
    would extract the real tree instead of the fixture's commit.
    """
    argv = [
        sys.executable,
        str(root / "tools" / "artifact_check.py"),
        sid,
        "HEAD",
        "--out-dir",
        str(out_dir),
    ]
    try:
        return subprocess.run(
            argv, cwd=str(root), env=_s115nd_env(), capture_output=True,
            text=True, timeout=S115ND_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"artifact_check {sid} exceeded {S115ND_TIMEOUT}s"
        raise AssertionError(msg) from exc


def _s115nd_git(root: Path, *argv: str) -> str:
    """One local git command in the fixture; nonzero is a build error."""
    proc = subprocess.run(
        ["git", "-C", str(root), *argv], capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"git {' '.join(argv)}: {proc.stdout}{proc.stderr}"
    return proc.stdout


def _s115nd_design(sid: str, ships: str) -> str:
    """The fixture DESIGN.md: one ships row whose cells the caller writes."""
    return (
        "# Fixture design\n\n"
        "A minimal check-compatible campaign used by the s115 w2 pins.\n\n"
        "| season | outcome | ships |\n"
        "|---|---|---|\n"
        f"| {sid} | WIN | {ships} |\n"
    )


def _s115nd_fixture(
    root: Path, sid: str, design: bool, pins: bool, row: bool = True,
    ships: str = "",
) -> Path:
    """Build a check-compatible fixture campaign at root and commit it.

    design=False omits DESIGN.md from the tree (the issues #36/#37
    no-convention case). row=False writes a DESIGN.md whose ships table
    has no row for sid (the tamper-sensitive case). With pins=True the
    tree carries two committed sanity pins. The ships cell must stay
    check-compatible: no key, slash, or suite tokens (the s57 w2
    convention).
    """
    (root / ".rumpun").mkdir(parents=True)
    (root / "src" / "rumpun").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "tools").mkdir()
    (root / ".rumpun" / "rumpun.yaml").write_text(
        "campaign: fixture\n", encoding="utf-8",
    )
    if design:
        text = (
            _s115nd_design(sid, ships)
            if row
            else _s115nd_design("fxother", "nothing here")
        )
        (root / "DESIGN.md").write_text(text, encoding="utf-8")
    (root / "src" / "rumpun" / "__init__.py").write_text(
        '__version__ = "0.0.0-fixture"\n', encoding="utf-8",
    )
    if pins:
        (root / "tests" / f"test_{sid}_sanity.py").write_text(
            FX_PINS_BODY, encoding="utf-8",
        )
    checker = _s115nd_repo() / "tools" / "artifact_check.py"
    (root / "tools" / "artifact_check.py").write_bytes(checker.read_bytes())
    _s115nd_git(root, "init", "-q")
    _s115nd_git(root, "add", "-A")
    _s115nd_git(
        root, "-c", "user.name=fx", "-c", "user.email=fx@example.com",
        "commit", "-qm", "fixture season",
    )
    listed = _s115nd_git(root, "ls-files")
    expected = [
        ".rumpun/rumpun.yaml", "src/rumpun/__init__.py",
        "tools/artifact_check.py",
    ]
    if design:
        expected.append("DESIGN.md")
    for needed in expected:
        assert needed in listed.splitlines(), f"fixture commit lost {needed}"
    if not design:
        assert "DESIGN.md" not in listed.splitlines(), (
            "the no-design fixture carries the convention it must lack"
        )
    return root


# --- spec 1: no convention and no pins lane -> named skip, exit 0 ------------


def test_s115nd_nodesign_nopins_named_skip(tmp_path: Path) -> None:
    """A tree with no DESIGN.md and no pins lane: named skip, exit 0, no record.

    fx01's extract carries no DESIGN.md and no tests/test_fx01_*.py, so
    nothing is checkable. The honest outcome is the named skip line
    naming the missing convention on the streams and a clean exit, not
    the structural refusal. Red today for the spec reason: current code
    refuses with exit 2 ("unreadable artifact ... DESIGN.md") and no
    named line, indistinguishable from tamper.
    """
    root = _s115nd_fixture(tmp_path / "fx", "fx01", design=False, pins=False)
    out_dir = tmp_path / "out"
    proc = _s115nd_run(root, "fx01", out_dir)
    streams = proc.stdout + proc.stderr
    assert proc.returncode == 0, streams
    assert "no DESIGN.md convention" in streams, streams
    assert "(nothing to check)" in streams, streams
    assert not (out_dir.exists() and any(out_dir.iterdir())), (
        "the skip writes no check record"
    )


# --- spec 2: no convention with a pins lane -> SHIPS skips, the rest binds ---


def test_s115nd_nodesign_with_pins_ships_skip_note(tmp_path: Path) -> None:
    """A tree with no DESIGN.md and a pins lane: record carries the note.

    fx02's extract carries no DESIGN.md but does carry
    tests/test_fx02_sanity.py, so the pins, pack digests, and seals can
    still bind; only the SHIPS phase has nothing to read. The honest
    outcome is exit 0, a record whose note names the missing convention,
    the pins run recorded, and verdict VERIFIED (the pins are green).
    Red today for the spec reason: current code refuses with exit 2
    before the pins ever run.
    """
    root = _s115nd_fixture(tmp_path / "fx", "fx02", design=False, pins=True)
    out_dir = tmp_path / "out"
    proc = _s115nd_run(root, "fx02", out_dir)
    streams = proc.stdout + proc.stderr
    assert proc.returncode == 0, streams
    records = sorted(out_dir.glob("*.md"))
    assert records, f"no check record written to {out_dir}:\n{streams}"
    record = records[0].read_text(encoding="utf-8")
    assert "no DESIGN.md convention" in record, record
    assert "verdict: VERIFIED" in record, record
    assert "2 passed" in record, record


# --- spec 3: a DESIGN.md present but missing the row still refuses ------------


def test_s115nd_design_present_missing_row_still_refuses(tmp_path: Path) -> None:
    """A DESIGN.md whose ships table has no row for the sid: exit 2 stands.

    fx03's extract carries a DESIGN.md whose ships table names only
    fxother, so the ships-row lookup for fx03 is the tamper-sensitive
    refusal issue #36 keeps: exit 2, naming the lookup. Green at HEAD
    (the refusal is current behavior): this pin holds the merge, not the
    red set.
    """
    root = _s115nd_fixture(
        tmp_path / "fx", "fx03", design=True, pins=False, row=False,
    )
    proc = _s115nd_run(root, "fx03", tmp_path / "out")
    streams = proc.stdout + proc.stderr
    assert proc.returncode == 2, streams
    assert "no ships row for fx03" in streams, streams


# --- spec 4: a repo WITH the convention is byte-unchanged ---------------------


def test_s115nd_with_convention_unchanged(tmp_path: Path) -> None:
    """A repo with the convention and a true pins claim: VERIFIED, no note.

    fx04's extract carries the DESIGN.md row and two sanity pins its
    cell truthfully claims; the record is today's VERIFIED shape, and
    the no-convention note never appears in it. Green at HEAD: this pin
    holds the merge, not the red set.
    """
    root = _s115nd_fixture(
        tmp_path / "fx", "fx04", design=True, pins=True,
        ships="tests/test_fx04_sanity.py exists; 2 pins",
    )
    out_dir = tmp_path / "out"
    proc = _s115nd_run(root, "fx04", out_dir)
    streams = proc.stdout + proc.stderr
    assert proc.returncode == 0, streams
    records = sorted(out_dir.glob("*.md"))
    assert records, f"no check record written to {out_dir}:\n{streams}"
    record = records[0].read_text(encoding="utf-8")
    assert "verdict: VERIFIED" in record, record
    assert "no DESIGN.md convention" not in record, record
    assert "2 passed" in record, record
