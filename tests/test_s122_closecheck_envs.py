"""s122 w2 pins: the close check survives bare environments.

Spec-first pins (red against current code) for the s122 w2 contract
(season goal seasons/s122.yaml; issues #39 and #40 on the checker's
environment seam, measured 2026-09-20):

- issue #39: the import probe refuses exit 2 when the extract has no
  src/. A pin-bearing season in a docs-only repo can never pass its
  pins lane. The contract: an extract with no src/ takes the named
  pins-lane skip, exit 0, no record. The skip line names the missing
  environment ("no src/ in the extract"), distinct from any tamper
  refusal.
- issue #40: the venv python falls back to sys.executable with no
  pytest probe. The pins lane dies "No module named pytest" exit 1 on
  green trees. The contract: the fallback probes pytest importability
  before use. A python without pytest is refused exit 2 with the named
  line ("no python with pytest"), before extraction, never silently
  used, and never a false DELTA on a green tree.

Repos with src/ and a real venv are byte-unchanged: the venv python is
returned unprobed and the VERIFIED path is untouched. Specs 4 and 5
hold that merge (green at HEAD). Fixture trees live in tmp; .rumpun/
runs/ is never copied. Measured red set:
.rumpun/runs/s122/w2/notes.md. Helpers carry the _s122env_ prefix. No
rumpun imports: subprocess and file reads only, plus one importlib
load of the checker module for the venv_python unit pins.
"""

from __future__ import annotations

import importlib.util
import logging
import subprocess
import sys
from pathlib import Path

import pytest

S122ENV_TIMEOUT = 240  # the checker's own pins bound; a timeout is a pin failure

FX_PINS_BODY = '''\
"""Fixture pins: two passing checks, no rumpun import needed."""


def test_fx_sanity_math() -> None:
    assert 1 + 1 == 2


def test_fx_sanity_text() -> None:
    assert "fx".upper() == "FX"
'''


def _s122env_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically solo and in-suite: both locate the same tree.
    """
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise AssertionError("no pyproject.toml above the pins file")


def _s122env_checker() -> Path:
    return _s122env_repo() / "tools" / "artifact_check.py"


def _s122env_load():
    """The checker module, loaded from the repo copy under a unique name.

    The module registers under its name before exec_module: dataclass
    creation looks the module up in sys.modules.
    """
    name = "artifact_check_s122env"
    spec = importlib.util.spec_from_file_location(name, _s122env_checker())
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _s122env_git(root: Path, *argv: str) -> str:
    """One local git command in the fixture; nonzero is a build error."""
    proc = subprocess.run(
        ["git", "-C", str(root), *argv], capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"git {' '.join(argv)}: {proc.stdout}{proc.stderr}"
    return proc.stdout


def _s122env_bare_python(tmp_path: Path) -> Path:
    """A real python with no pytest: a pip-less venv off the runner.

    The no-pytest property is proven here, not assumed: the probe the
    checker uses (import pytest) must fail on this interpreter.
    """
    venv_dir = tmp_path / "bare"
    proc = subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(venv_dir)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"venv build: {proc.stdout}{proc.stderr}"
    python = venv_dir / "bin" / "python"
    assert python.is_file()
    probe = subprocess.run(
        [str(python), "-c", "import pytest"], capture_output=True, text=True,
    )
    assert probe.returncode != 0, "the bare venv unexpectedly imports pytest"
    return python


def _s122env_run(
    root: Path, sid: str, out_dir: Path, python_argv: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """One bounded checker subprocess run: sid @ HEAD, record into out_dir.

    python_argv is the interpreter prefix, default [sys.executable]. The
    fixture's own checker copy runs, not the repo's: the checker
    resolves the repo from its own file location, so the repo's copy
    would extract the real tree instead of the fixture's commit.
    """
    argv = [
        *(python_argv if python_argv is not None else [sys.executable]),
        str(root / "tools" / "artifact_check.py"),
        sid,
        "HEAD",
        "--out-dir",
        str(out_dir),
    ]
    try:
        return subprocess.run(
            argv, cwd=str(root), capture_output=True, text=True,
            timeout=S122ENV_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"artifact_check {sid} exceeded {S122ENV_TIMEOUT}s"
        raise AssertionError(msg) from exc


def _s122env_design(sid: str, ships: str) -> str:
    """The fixture DESIGN.md: one ships row whose cell the caller writes."""
    return (
        "# Fixture design\n\n"
        "A minimal check-compatible campaign used by the s122 w2 pins.\n\n"
        "| season | outcome | ships |\n"
        "|---|---|---|\n"
        f"| {sid} | WIN | {ships} |\n"
    )


def _s122env_fixture(
    root: Path, sid: str, ships: str, *, src: bool = True, pins: bool = True,
    design: bool = True,
) -> Path:
    """Build a check-compatible fixture campaign at root and commit it.

    src=False leaves the package out (a docs-only repo). design=False
    leaves the DESIGN.md convention out. The ships cell must stay
    check-compatible: no key, slash, or suite tokens (the s57 w2
    convention).
    """
    root.mkdir()
    (root / ".rumpun").mkdir()
    (root / "tests").mkdir()
    (root / "tools").mkdir()
    (root / ".rumpun" / "rumpun.yaml").write_text(
        "campaign: fixture\n", encoding="utf-8",
    )
    (root / "README.md").write_text("fixture campaign\n", encoding="utf-8")
    if design:
        (root / "DESIGN.md").write_text(
            _s122env_design(sid, ships), encoding="utf-8",
        )
    if src:
        (root / "src" / "rumpun").mkdir(parents=True)
        (root / "src" / "rumpun" / "__init__.py").write_text(
            '__version__ = "0.0.0-fixture"\n', encoding="utf-8",
        )
    if pins:
        (root / "tests" / f"test_{sid}_sanity.py").write_text(
            FX_PINS_BODY, encoding="utf-8",
        )
    (root / "tools" / "artifact_check.py").write_bytes(
        _s122env_checker().read_bytes(),
    )
    _s122env_git(root, "init", "-q")
    _s122env_git(root, "add", "-A")
    _s122env_git(
        root, "-c", "user.name=fx", "-c", "user.email=fx@example.com",
        "commit", "-qm", "fixture season",
    )
    listed = _s122env_git(root, "ls-files").splitlines()
    for needed in (
        ".rumpun/rumpun.yaml", "README.md", "tools/artifact_check.py",
    ):
        assert needed in listed, f"fixture commit lost {needed}"
    return root


# --- spec 1 (issue #39): no-src extract takes the named skip -----------------


def test_s122env_no_src_extract_takes_named_skip(tmp_path: Path) -> None:
    """Docs-only extract with a pins lane: named skip, exit 0, no record.

    The extract carries a committed pins file, no src/, and no DESIGN.md.
    Today the import probe refuses exit 2 ("import probe failed"),
    indistinguishable from tamper, so the close can never pass. The
    contract: the named skip line fires instead, exit 0, no record.
    """
    root = _s122env_fixture(
        tmp_path / "fx", "fx01", "sanity pins committed",
        src=False, design=False,
    )
    out_dir = tmp_path / "out"
    proc = _s122env_run(root, "fx01", out_dir)
    streams = proc.stdout + proc.stderr
    assert proc.returncode == 0, streams
    assert "no src/ in the extract" in streams, streams
    assert "import probe failed" not in streams, streams
    assert not (out_dir.exists() and any(out_dir.iterdir())), (
        "the skip writes no check record"
    )


# --- spec 2 (issue #40): the fallback python is probed -----------------------


def test_s122env_fallback_without_pytest_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture,
) -> None:
    """venv_python with no .venv and a pytest-less fallback: exit 2 refusal.

    The fallback interpreter is a real python that truly cannot import
    pytest (proven in the helper). Today venv_python returns it unprobed;
    the contract: a refusal naming the gap ("no python with pytest",
    "cannot import pytest"), never a silent return.
    """
    checker = _s122env_load()
    bare = _s122env_bare_python(tmp_path)
    repo = tmp_path / "repo"  # deliberately holds no .venv
    repo.mkdir()
    monkeypatch.setattr(sys, "executable", str(bare))
    with (
        caplog.at_level(logging.ERROR, logger="artifact_check"),
        pytest.raises(SystemExit) as exc,
    ):
        checker.venv_python(repo)
    assert exc.value.code == 2
    assert "no python with pytest" in caplog.text, caplog.text
    assert "cannot import pytest" in caplog.text, caplog.text


def test_s122env_real_venv_python_returned_unprobed(tmp_path: Path) -> None:
    """A repo with a real venv: venv_python returns it, byte-unchanged path.

    Green at HEAD. Holds the merge: the s122 w2 change adds a probe to
    the fallback branch only, so the venv-present branch must stay
    return-without-probe.
    """
    checker = _s122env_load()
    repo = tmp_path / "repo"
    venv_bin = repo / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    venv_py = venv_bin / "python"
    venv_py.symlink_to(sys.executable)
    assert checker.venv_python(repo) == str(venv_py)


# --- spec 3 (issue #40): the false delta becomes the named refusal -----------


def test_s122env_false_delta_becomes_named_refusal(tmp_path: Path) -> None:
    """Bare-python checker run on a src-bearing green tree: refusal, no DELTA.

    The checker runs under a real pytest-less python against a fixture
    with src/, committed pins, and a true pins claim. Today the pins lane
    dies "No module named pytest" exit 1, a false DELTA with a record on
    a green tree. The contract: exit 2 with the named line, before
    extraction, no record written.
    """
    root = _s122env_fixture(
        tmp_path / "fx", "fx03",
        "tests/test_fx03_sanity.py exists; 2 pins",
    )
    bare = _s122env_bare_python(tmp_path)
    out_dir = tmp_path / "out"
    proc = _s122env_run(root, "fx03", out_dir, python_argv=[str(bare)])
    streams = proc.stdout + proc.stderr
    assert proc.returncode == 2, streams
    assert "no python with pytest" in streams, streams
    assert "cannot import pytest" in streams, streams
    assert not (out_dir.exists() and any(out_dir.iterdir())), (
        "the refusal precedes extraction; no record is written"
    )


# --- spec 5: the VERIFIED path with a real venv is untouched -----------------


def test_s122env_verified_path_with_real_venv_unchanged(tmp_path: Path) -> None:
    """src-bearing fixture with a real venv: VERIFIED, exit 0, record.

    Green at HEAD. Holds the byte-unchanged claim at the E2E level: the
    venv python runs the committed pins and the record carries the
    2-passed count.
    """
    root = _s122env_fixture(
        tmp_path / "fx", "fx04",
        "tests/test_fx04_sanity.py exists; 2 pins",
    )
    venv_bin = root / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    # A naked symlink to the repo venv python resolves past pyvenv.cfg to
    # the base interpreter (no pytest there). The shim execs the repo
    # venv python, so the "venv" really runs pytest.
    shim = venv_bin / "python"
    shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
    shim.chmod(0o755)
    out_dir = tmp_path / "out"
    proc = _s122env_run(root, "fx04", out_dir)
    streams = proc.stdout + proc.stderr
    assert proc.returncode == 0, streams
    records = sorted(out_dir.glob("*.md"))
    assert records, f"no check record written to {out_dir}:\n{streams}"
    record = records[0].read_text(encoding="utf-8")
    assert "verdict: VERIFIED" in record, record
    assert "2 passed" in record, record
