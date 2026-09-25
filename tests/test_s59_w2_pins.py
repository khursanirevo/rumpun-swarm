"""s59 w2 pins — the close-check fallback, pinned.

SPEC-FIRST PINS, HARNESS-REPAIRED (2026-09-16): w2 was terminated
mid-write (the season ended stopped_stall) and the file's helper defs
and pin bodies were corrupted; the harness rebuilt the file from the
recovered spec (the docstrings, asserts, and constants survived). The
red set was re-measured at the merge; the graft note below is w2's own.

The contract (seasons/s59.yaml + w1's brief): the checker extracts
<close-commit> with git archive and judges the extracted tree. s59 adds
one fallback to the ships-row lookup: when the extracted DESIGN.md has
no row for <sid> but the live worktree DESIGN.md (REPO/DESIGN.md, the
--repo root) has one, the live row is used and the record discloses it
with the exact line "ships row read from the live worktree (the close's
own entry postdates the commit)". The fallback covers ONLY the missing
fresh ships row: pins, pack digests, harvest seals, and the ships diff
still bind to the extracted tree, so a tampered tree yields DELTA exit 1
with the fallback in play. When both sources carry the row, the
extracted row wins byte-for-byte and the record carries no disclosure
line.

Every pin builds its own miniature git campaign under pytest tmp_path
(git init, one close commit, the fresh row left uncommitted in the
working tree) and runs the checker as a bounded subprocess with --repo
and --out-dir pointed inside the fixture. No pin ever writes the real
repo: the real ledger is untouched, records land in tmp out-dirs.

Graft: land this file in tests/ as-is (additions-only; existing suite
files stay untouched). Helpers carry the _s59w2_ prefix, so nothing
collides with existing defs.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

S59W2_TIMEOUT = 240  # the spec bound for one checker run

S59W2_SID = "s59x"  # fixture season id; matches no real season row

# w1's brief names this exact disclosure line; the record carries it
# verbatim whenever the live-row fallback fires.
S59W2_DISCLOSURE = (
    "ships row read from the live worktree"
    " (the close's own entry postdates the commit)"
)

S59W2_OLD_CELL = "an older season's landed ships, kept for table shape"

S59W2_GREEN_CELL = (
    "the pins file tests/test_s59x_pins.py exists, suite 1/1 recorded"
)

S59W2_GHOST_CELL = (
    "the pins file tests/test_s59x_pins.py exists, "
    "the ghost file tests/test_ghost.py exists too"
)

S59W2_PIN_FILE = (
    "def test_s59x_fixture_pin() -> None:\n"
    "    \"\"\"The fixture season's own green pin (stdlib-only).\"\"\"\n"
    "    assert True\n"
)


def _s59w2_root() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and
    grafted into tests/ (post-graft): both sit under a pyproject.toml
    root.
    """
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise AssertionError("no pyproject.toml above the pins file")


def _s59w2_row(sid: str, cell: str) -> str:
    """One DESIGN.md outcome row: | <sid> | outcome | ships |."""
    return f"| {sid} | WIN (all band clauses met) | {cell} |"


def _s59w2_design(*rows: str) -> str:
    """A minimal DESIGN.md body: the campaign-log header plus the rows."""
    head = (
        "# fixture design\n\n## 15. campaign log\n\n"
        "| season | outcome | ships |\n|---|---|---|\n"
    )
    return head + "\n".join(rows) + "\n"


def _s59w2_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _s59w2_git(repo: Path, *argv: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *argv], capture_output=True, text=True,
        timeout=S59W2_TIMEOUT,
    )
    assert proc.returncode == 0, f"git {' '.join(argv)} failed: {proc.stderr}"
    return proc.stdout


def _s59w2_fixture(
    tmp: Path, committed: str, live: str, packs: bool = False,
) -> tuple[Path, str]:
    """A miniature campaign repo under tmp.

    HEAD carries committed as DESIGN.md; the working tree carries live as
    DESIGN.md (uncommitted — the just-closed entry). The tree always
    carries src/rumpun/__init__.py (the import probe's target) and
    tests/test_s59x_pins.py (one green pin). packs=True adds a committed
    .rumpun pack whose claimed digest cannot be recomputed (the
    tampered-digest world). Returns (repo, close sha).
    """
    repo = tmp / "fx"
    _s59w2_write(
        repo / "src" / "rumpun" / "__init__.py", '__version__ = "s59w2-fixture"\n',
    )
    _s59w2_write(repo / "tests" / f"test_{S59W2_SID}_pins.py", S59W2_PIN_FILE)
    _s59w2_write(repo / "DESIGN.md", committed)
    if packs:
        _s59w2_write(
            repo / ".rumpun" / "plugins.yml",
            "plugins:\n  pack-fx:\n    digest: " + "f" * 64 + "\n",
        )
        _s59w2_write(
            repo / ".rumpun" / "plugins" / "pack-fx" / "priors" / "earlier.txt",
            "tampered pack content\n",
        )
    _s59w2_git(repo, "init")
    _s59w2_git(repo, "add", "-A")
    _s59w2_git(
        repo, "-c", "user.email=s59w2@fixture", "-c", "user.name=s59w2",
        "commit", "-m", "close",
    )
    sha = _s59w2_git(repo, "rev-parse", "HEAD").strip()
    _s59w2_write(repo / "DESIGN.md", live)
    return repo, sha


def _s59w2_check(repo: Path, sha: str, out_dir: Path) -> subprocess.CompletedProcess[str]:
    """One bounded checker run: --repo and --out-dir inside the fixture
    world, so the real repo is read-only for the pins."""
    runner = _s59w2_root() / "tools" / "artifact_check.py"
    venv = _s59w2_root() / ".venv" / "bin" / "python"
    python = str(venv) if venv.is_file() else sys.executable
    argv = [
        python, str(runner), S59W2_SID, sha,
        "--repo", str(repo), "--out-dir", str(out_dir),
    ]
    try:
        return subprocess.run(
            argv, capture_output=True, text=True, timeout=S59W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"artifact_check exceeded {S59W2_TIMEOUT}s"
        raise AssertionError(msg) from exc


def _s59w2_record(out_dir: Path) -> str:
    """The single check record the run landed (or an assert naming it)."""
    matches = sorted(out_dir.glob(f"*check-{S59W2_SID}.md"))
    assert len(matches) == 1, f"expected one record in {out_dir}: {matches}"
    return matches[0].read_text(encoding="utf-8")


def test_s59w2_close_case_checks_through_with_disclosure(tmp_path: Any) -> None:
    """A fresh close checks through: exit 0, VERIFIED, the record lands
    with the live-row disclosure line.

    The close commit's DESIGN.md cannot carry the season's own entry
    (s57's live fire: exit 2 on every fresh close). The fallback reads
    the uncommitted live row, the record discloses it, and an otherwise
    green tree is VERIFIED.
    """
    committed = _s59w2_design(_s59w2_row("s59w", S59W2_OLD_CELL))
    live = _s59w2_design(
        _s59w2_row("s59w", S59W2_OLD_CELL), _s59w2_row(S59W2_SID, S59W2_GREEN_CELL),
    )
    repo, sha = _s59w2_fixture(tmp_path / "fx", committed, live)
    out_dir = tmp_path / "out"
    proc = _s59w2_check(repo, sha, out_dir)
    streams = proc.stdout + "\n" + proc.stderr
    assert proc.returncode == 0, streams[-2000:]
    record = _s59w2_record(out_dir)
    assert S59W2_DISCLOSURE in record, record
    assert "verdict: VERIFIED" in record, record
    assert f"ships row (verbatim): {S59W2_GREEN_CELL}" in record, record


def test_s59w2_ghost_ships_file_stays_delta_under_fallback(tmp_path: Any) -> None:
    """A ghost ships file claims a file the extracted tree lacks.

    The fallback is in play (the row exists only in the live worktree),
    and the ships diff still binds to the extracted tree: DELTA, exit 1,
    the record lands with the disclosure line and names the missing file.
    """
    committed = _s59w2_design(_s59w2_row("s59w", S59W2_OLD_CELL))
    live = _s59w2_design(
        _s59w2_row("s59w", S59W2_OLD_CELL), _s59w2_row(S59W2_SID, S59W2_GHOST_CELL),
    )
    repo, sha = _s59w2_fixture(tmp_path / "fx", committed, live)
    out_dir = tmp_path / "out"
    proc = _s59w2_check(repo, sha, out_dir)
    streams = proc.stdout + "\n" + proc.stderr
    assert proc.returncode == 1, streams[-2000:]
    record = _s59w2_record(out_dir)
    assert S59W2_DISCLOSURE in record, record
    assert "verdict: DELTA" in record, record
    assert "missing file: tests/test_ghost.py" in record, record
    assert f"ships row (verbatim): {S59W2_GHOST_CELL}" in record, record


def test_s59w2_bad_pack_digest_stays_delta_under_fallback(tmp_path: Any) -> None:
    """A claimed pack digest the extracted tree cannot reproduce.

    Same close world, plus a committed .rumpun pack whose claimed digest
    cannot be recomputed. The green live row must not launder it: DELTA,
    exit 1, the record carries the disclosure line and the digest delta.
    """
    committed = _s59w2_design(_s59w2_row("s59w", S59W2_OLD_CELL))
    live = _s59w2_design(
        _s59w2_row("s59w", S59W2_OLD_CELL), _s59w2_row(S59W2_SID, S59W2_GREEN_CELL),
    )
    repo, sha = _s59w2_fixture(tmp_path / "fx", committed, live, packs=True)
    out_dir = tmp_path / "out"
    proc = _s59w2_check(repo, sha, out_dir)
    streams = proc.stdout + "\n" + proc.stderr
    assert proc.returncode == 1, streams[-2000:]
    record = _s59w2_record(out_dir)
    assert S59W2_DISCLOSURE in record, record
    assert "verdict: DELTA" in record, record
    assert "pack digest pack-fx" in record, record
    assert "-> DELTA" in record, record
    assert f"ships row (verbatim): {S59W2_GREEN_CELL}" in record, record


def test_s59w2_extracted_row_wins_when_both_sources_have_it(tmp_path: Any) -> None:
    """Both sources carry the row: the extracted row wins byte-for-byte
    and no disclosure line appears.

    The live worktree's row claims a ghost file; a fallback that fired
    would DELTA. The extracted green row wins instead: exit 0, VERIFIED,
    the verbatim line equals the extracted cell, and the record carries
    no disclosure line and no ghost token.
    """
    committed = _s59w2_design(
        _s59w2_row("s59w", S59W2_OLD_CELL), _s59w2_row(S59W2_SID, S59W2_GREEN_CELL),
    )
    live = _s59w2_design(
        _s59w2_row("s59w", S59W2_OLD_CELL), _s59w2_row(S59W2_SID, S59W2_GHOST_CELL),
    )
    repo, sha = _s59w2_fixture(tmp_path / "fx", committed, live)
    out_dir = tmp_path / "out"
    proc = _s59w2_check(repo, sha, out_dir)
    streams = proc.stdout + "\n" + proc.stderr
    assert proc.returncode == 0, streams[-2000:]
    record = _s59w2_record(out_dir)
    assert S59W2_DISCLOSURE not in record, record
    assert "verdict: VERIFIED" in record, record
    assert f"ships row (verbatim): {S59W2_GREEN_CELL}" in record, record
    assert "test_ghost.py" not in record, record
