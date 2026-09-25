"""s108 w2 pins — the close check learns the pinless skip.

Spec-first pins (red against current code) for the s108 w2 contract
(season goal seasons/s108.yaml; the s107 close's ride-along check
refused structurally, exit 2, because the season shipped no pins lane,
and the note was recorded non-authoritative; a pinless close is
legitimate and must skip with a named reason, not refuse). Measured red
set: .rumpun/runs/s108/w2/notes.md.

The contract these pins hold: the checker behind `rumpun check`
(tools/artifact_check.py) refuses with exit 2 when the season has no
pins files AND the ships row claims pins (a real delta; the glob line
stays on the stderr). When no pins files exist and the ships row claims
none, the check skips with the named line "no pins lane (nothing to
check)" and exits clean, writing no record. The existing VERIFIED path
is untouched. Grafting: land this file in tests/ as-is (additions-only;
existing suite files stay untouched). Helpers carry the _s108check_
prefix, so nothing collides with existing defs. No rumpun imports:
subprocess and file reads only.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

S108CHECK_TIMEOUT = 240  # the checker's own pins bound; a timeout is a pin failure

FX_PINS_BODY = '''\
"""Fixture pins: two passing checks, no rumpun import needed."""


def test_fx_sanity_math() -> None:
    assert 1 + 1 == 2


def test_fx_sanity_text() -> None:
    assert "fx".upper() == "FX"
'''


def _s108check_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically pre-graft (the w2 workspace) and post-graft
    (tests/): both sit under the repo root.
    """
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise AssertionError("no pyproject.toml above the pins file")


def _s108check_env() -> dict[str, str]:
    """The subprocess env: repo src/ on PYTHONPATH ahead of any inherited value."""
    env = dict(os.environ)
    src = str(_s108check_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s108check_run(
    root: Path, sid: str, out_dir: Path,
) -> subprocess.CompletedProcess[str]:
    """One bounded checker subprocess run: sid @ HEAD, record into out_dir.

    The fixture's own checker copy runs, not the repo's: the checker
    resolves the repo from its own file location, so the repo's copy
    would extract the real tree (the 1183-file pull the first red run
    showed) instead of the fixture's commit.
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
            argv, cwd=str(root), env=_s108check_env(), capture_output=True,
            text=True, timeout=S108CHECK_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"artifact_check {sid} exceeded {S108CHECK_TIMEOUT}s"
        raise AssertionError(msg) from exc


def _s108check_git(root: Path, *argv: str) -> str:
    """One local git command in the fixture; nonzero is a build error."""
    proc = subprocess.run(
        ["git", "-C", str(root), *argv], capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"git {' '.join(argv)}: {proc.stdout}{proc.stderr}"
    return proc.stdout


def _s108check_design(sid: str, ships: str) -> str:
    """The fixture DESIGN.md: one ships row whose cell the caller writes."""
    return (
        "# Fixture design\n\n"
        "A minimal check-compatible campaign used by the s108 w2 pins.\n\n"
        "| season | outcome | ships |\n"
        "|---|---|---|\n"
        f"| {sid} | WIN | {ships} |\n"
    )


def _s108check_fixture(root: Path, sid: str, ships: str, pins: bool) -> Path:
    """Build a check-compatible fixture campaign at root and commit it.

    The ships cell must stay check-compatible: no key, slash, or suite
    tokens (the s57 w2 convention). With pins=True the tree carries two
    committed sanity pins; the caller's ships cell claims them.
    """
    (root / ".rumpun").mkdir(parents=True)
    (root / "src" / "rumpun").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "tools").mkdir()
    (root / ".rumpun" / "rumpun.yaml").write_text(
        "campaign: fixture\n", encoding="utf-8",
    )
    (root / "DESIGN.md").write_text(_s108check_design(sid, ships), encoding="utf-8")
    (root / "src" / "rumpun" / "__init__.py").write_text(
        '__version__ = "0.0.0-fixture"\n', encoding="utf-8",
    )
    if pins:
        (root / "tests" / f"test_{sid}_sanity.py").write_text(
            FX_PINS_BODY, encoding="utf-8",
        )
    checker = _s108check_repo() / "tools" / "artifact_check.py"
    (root / "tools" / "artifact_check.py").write_bytes(checker.read_bytes())
    _s108check_git(root, "init", "-q")
    _s108check_git(root, "add", "-A")
    _s108check_git(
        root, "-c", "user.name=fx", "-c", "user.email=fx@example.com",
        "commit", "-qm", "fixture season",
    )
    listed = _s108check_git(root, "ls-files")
    for needed in (
        "DESIGN.md", ".rumpun/rumpun.yaml", "src/rumpun/__init__.py",
        "tools/artifact_check.py",
    ):
        assert needed in listed.splitlines(), f"fixture commit lost {needed}"
    return root


# --- spec 1: the pinless close skips with a named reason ---------------------


def test_s108check_pinless_season_skips_with_named_reason(tmp_path: Path) -> None:
    """A season with no pins files and no pins claim: skip line, exit 0, no record.

    fx01's ships cell names no pins and the tree carries no
    tests/test_fx01_*.py, so the check has nothing to bite. The honest
    outcome is the named skip on the streams and a clean exit, not the
    structural refusal. Red today for the spec reason: current code
    refuses every pinless season with exit 2 and no skip line.
    """
    root = _s108check_fixture(
        tmp_path / "fx", "fx01",
        "the season ships no pins lane; nothing to check",
        pins=False,
    )
    out_dir = tmp_path / "out"
    proc = _s108check_run(root, "fx01", out_dir)
    streams = proc.stdout + proc.stderr
    assert proc.returncode == 0, streams
    assert "no pins lane (nothing to check)" in streams, streams
    assert not (out_dir.exists() and any(out_dir.iterdir())), (
        "the skip writes no check record"
    )


# --- spec 2: the refusal stays for a real delta -------------------------------


def test_s108check_claimed_pins_without_files_still_refuse(tmp_path: Path) -> None:
    """A season whose ships row claims pins with no pins files: exit 2.

    fx02 claims 3 pins and ships none, so the structural refusal is the
    honest outcome and must survive the s108 change. Green at HEAD (the
    refusal is current behavior): this pin holds the merge, not the red
    set. The refusal line keeps naming the glob.
    """
    root = _s108check_fixture(
        tmp_path / "fx", "fx02", "the season ships 3 pins", pins=False,
    )
    proc = _s108check_run(root, "fx02", tmp_path / "out")
    streams = proc.stdout + proc.stderr
    assert proc.returncode == 2, streams
    assert "no pins file matching tests/test_fx02_*.py" in streams, streams


# --- spec 3: the VERIFIED path is untouched -----------------------------------


def test_s108check_verified_path_untouched(tmp_path: Path) -> None:
    """A season with committed pins and a true claim: VERIFIED, exit 0.

    fx03 ships two sanity pins and its cell claims exactly them; the
    record lands in --out-dir with verdict VERIFIED and the 2-passed
    count. Green at HEAD: this pin holds the merge, not the red set.
    """
    root = _s108check_fixture(
        tmp_path / "fx", "fx03",
        "tests/test_fx03_sanity.py exists; 2 pins",
        pins=True,
    )
    out_dir = tmp_path / "out"
    proc = _s108check_run(root, "fx03", out_dir)
    streams = proc.stdout + proc.stderr
    assert proc.returncode == 0, streams
    records = sorted(out_dir.glob("*.md"))
    assert records, f"no check record written to {out_dir}:\n{streams}"
    record = records[0].read_text(encoding="utf-8")
    assert "verdict: VERIFIED" in record, record
    assert "2 passed" in record, record
