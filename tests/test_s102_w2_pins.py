"""s102 w2 pins — the scaffold ships the checker (issue #20).

The khursani campaign (v0.11.0) scaffolded without tools/artifact_check.py;
every harvest errored checker-not-found and the close-time check exited 2;
the workaround was a manual copy from the source repo. Reproduced on current
main before the fix (/tmp/s102w2-repro, 2026-09-18): `rumpun init` emits 15
files, none under tools/, and a strict close of a terminal s1 logs
"ERROR checker not found: <camp>/tools/artifact_check.py (repo <camp>)" and
exits 2. The fix: scaffold.init_project resolves the source tree's checker
(walk-up from the module, the lint._load_design_checker convention) BEFORE
any write lands and copies it to <target>/tools/artifact_check.py.

Contract these pins hold:
1. `rumpun init` emits the checker: a subprocess init into a fresh tmp
   campaign leaves tools/artifact_check.py in place, byte-identical to the
   source tree's checker (cmp over the bytes).
2. The emitted file passes ruff check --no-respect-gitignore. Binary
   resolution: repo .venv/bin/ruff, then ~/.local/bin/ruff, then PATH; a
   missing binary is a pin failure, never a skip.
3. The harvest close-time check finds it: a terminal s1 closes in the
   scaffolded campaign and the close runs the checker subprocess (the
   "check s1 @ HEAD -> <path>" spawn line in stderr, naming the shipped
   file) with no "checker not found" refusal; the close's books land (the
   s1-harvest ledger record and the verdicts row). No --strict: the
   close's exit reflects the harvest alone; the checker's artifact
   verdict is the s55/s57 contract, not this issue's.

Fixture discipline: everything lives under pytest tmp_path; no pin writes
the real ledger; the subprocess env carries repo src/ on PYTHONPATH ahead
of any inherited value; a timeout is a pin failure, not a hang (the s57 w2
harness conventions). Helpers carry the _s102w2_ prefix, so nothing
collides with existing defs. Offline: git is never invoked; the fixture
campaign is not a git repo, so the spawned checker refuses at the extract
step — that refusal is the s55 checker's contract, not this issue's; this
pin's contract is only that the runner was FOUND and spawned.

Measured (solo run, /tmp/s102w2-pins-run1.log, 2026-09-18): 3 passed,
rc=0, 2.31s; ruff --no-respect-gitignore clean on scaffold.py and this
file. E2E measured before the pins (/tmp/s102w2-fixed-close.log):
init_exit=0, checker byte-identical to the source, close exit 0 with the
"check s1 @ HEAD -> <camp>/tools/artifact_check.py" spawn line and no
checker-not-found refusal.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

S102W2_TIMEOUT = 240  # the spec bound for one harness subprocess, s57 w2 convention
S102W2_IMPLIES = "s102w2 fixture close: the scaffold ships the checker"

S102W2_STATE = {
    "id": "s1",
    "status": "completed",
    "started_at": 1789000000.0,
    "ended_at": 1789000005.0,
    "stall_s": 2700.0,
    "agents": {},
}


def _s102w2_repo() -> Path:
    """Repo root: the first ancestor of this file holding pyproject.toml."""
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s102w2_env() -> dict[str, str]:
    """Subprocess env: repo src/ on PYTHONPATH ahead of any inherited value."""
    env = dict(os.environ)
    src = str(_s102w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s102w2_run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """One bounded subprocess run; a timeout is a pin failure, not a hang."""
    try:
        return subprocess.run(
            argv, cwd=str(cwd), env=_s102w2_env(), capture_output=True,
            text=True, timeout=S102W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"{' '.join(argv[1:4])} exceeded {S102W2_TIMEOUT}s"
        raise AssertionError(msg) from exc


def _s102w2_init(camp: Path) -> subprocess.CompletedProcess[str]:
    """`rumpun init <camp>` as a real subprocess against repo src/."""
    return _s102w2_run(camp.parent, [sys.executable, "-m", "rumpun", "init", str(camp)])


def _s102w2_close_ready(camp: Path) -> None:
    """Terminal s1 state, the engine's completed shape, under the campaign."""
    state_dir = camp / ".rumpun" / "runs" / "s1" / "_season"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text(
        json.dumps(S102W2_STATE), encoding="utf-8"
    )


def _s102w2_ruff() -> str:
    """The ruff binary: repo .venv, then ~/.local/bin, then PATH; else fail."""
    repo = _s102w2_repo()
    for candidate in (
        repo / ".venv" / "bin" / "ruff",
        Path.home() / ".local" / "bin" / "ruff",
    ):
        if candidate.is_file():
            return str(candidate)
    which = shutil.which("ruff")
    if which:
        return which
    pytest.fail("no ruff binary: repo .venv/bin/ruff, ~/.local/bin/ruff, PATH")


def test_s102w2_init_emits_the_checker(tmp_path) -> None:
    """`rumpun init` ships tools/artifact_check.py, byte-identical to source."""
    camp = tmp_path / "camp"
    camp.mkdir()
    proc = _s102w2_init(camp)
    assert proc.returncode == 0, f"init rc={proc.returncode}: {proc.stderr}"
    shipped = camp / "tools" / "artifact_check.py"
    assert shipped.is_file(), f"no shipped checker: {sorted(p.name for p in camp.rglob('*'))[:20]}"
    source = _s102w2_repo() / "tools" / "artifact_check.py"
    assert source.is_file(), f"source checker missing: {source}"
    assert shipped.read_bytes() == source.read_bytes(), (
        "shipped checker differs from the source tree's checker"
    )


def test_s102w2_emitted_checker_passes_ruff(tmp_path) -> None:
    """The shipped checker passes the repo's own lint bar (ruff)."""
    camp = tmp_path / "camp"
    camp.mkdir()
    proc = _s102w2_init(camp)
    assert proc.returncode == 0, f"init rc={proc.returncode}: {proc.stderr}"
    shipped = camp / "tools" / "artifact_check.py"
    assert shipped.is_file(), "init shipped no checker; pin 1 precondition"
    ruff = _s102w2_ruff()
    lint = _s102w2_run(
        camp.parent, [ruff, "check", "--no-respect-gitignore", str(shipped)]
    )
    assert lint.returncode == 0, f"ruff rc={lint.returncode}: {lint.stdout}{lint.stderr}"


def test_s102w2_close_check_finds_the_checker(tmp_path) -> None:
    """The close's check spawns the shipped checker; no checker-not-found."""
    camp = tmp_path / "camp"
    camp.mkdir()
    proc = _s102w2_init(camp)
    assert proc.returncode == 0, f"init rc={proc.returncode}: {proc.stderr}"
    _s102w2_close_ready(camp)
    close = _s102w2_run(
        camp,
        [
            sys.executable, "-m", "rumpun", "harvest", "s1",
            "--verdict", "WIN", "--implies", S102W2_IMPLIES,
        ],
    )
    combined = close.stdout + close.stderr
    assert close.returncode == 0, f"close rc={close.returncode}: {combined}"
    assert "checker not found" not in combined, combined
    runner_line = f"check s1 @ HEAD -> {camp / 'tools' / 'artifact_check.py'}"
    assert runner_line in combined, combined
    records = list((camp / ".rumpun" / "ledger").glob("*s1-harvest.md"))
    assert records, "no s1-harvest ledger record"
    verdicts = camp / ".rumpun" / "runs" / "s1" / "verdicts.jsonl"
    assert verdicts.is_file(), "no verdicts row"
    rows = [
        json.loads(line)
        for line in verdicts.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(row.get("season") == "s1" for row in rows), rows
