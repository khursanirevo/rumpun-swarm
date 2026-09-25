"""s103 w2 pins -- the scaffold's emission contract, pinned from the other side.

w1's s102 fix changed what init emits: the spawnable plural (agents:) and the
shipped checker (tools/artifact_check.py). w1's pins (tests/test_s102_w1_pins.py,
tests/test_s102_w2_pins.py) hold the red-first shape. These are the never-again
pins: the emission contract must hold under the shapes the khursani campaign
literally used -- the singular `agent:` in the evaluate phase, the tools/ absence.

Ground truth measured 2026-09-18 on current main: the scaffold constants carry
zero singular `agent:` keys and six plural `agents:` group references (grep on
scaffold.py); tools/artifact_check.py itself is free of the substring `agent:`;
_checker_source() walks up from the module dir for tools/artifact_check.py and
raises ScaffoldError naming the walk-up root when the file is absent;
init_project resolves the checker BEFORE any write lands; the checker dest is
guarded by an explicit refuse-overwrite check ahead of the copy.

Contract these pins hold (offline: tmp_path, in-process init, no network, no git):
1. ZERO singular `agent:` keys anywhere in the emitted tree, grep-shape over
   every emitted file (block and list-item key forms, any indent).
2. The checker is byte-real: byte-identical to the source tree's checker and
   clean under ruff check --no-respect-gitignore. Binary resolution: repo
   .venv/bin/ruff, then ~/.local/bin/ruff, then PATH; a missing binary is a
   pin failure, never a skip.
3. The sourceless tree: with the walk-up source hidden (the module __file__
   pointed at an isolated fake tree under tmp_path; the real repo file is
   never moved or renamed, monkeypatch auto-restores), _checker_source()
   raises ScaffoldError naming tools/artifact_check.py, and init_project
   raises before any write lands.
4. The refuse-overwrite discipline holds: re-init into a scaffolded campaign
   refuses and the tree is byte-unchanged; a pre-existing checker destination
   is refused with its sentinel bytes intact (the guard precedes the copy;
   the .rumpun writes land first -- current behavior, pinned as such).
Measured (solo run 1, /tmp/s103w2-pins-run1.log, 2026-09-18): 5 passed, rc=0,
0.31s, ruff --no-respect-gitignore clean on this file. Run 2 gates the
post-edit file; the run record and pin map live in the s103 w2 notes.md.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from rumpun import scaffold

S103W2_TIMEOUT = 240  # one lint subprocess bound (the s102w2 convention)

# The khursani defect shape: a singular `agent:` key, block or list-item form,
# at any indent. `agents:` cannot match: the byte after `agent` is `s`.
S103W2_SINGULAR_AGENT = re.compile(r"^\s*(?:-\s+)*agent:(?=\s|$)", re.MULTILINE)

# The grep must be provably non-vacuous: these emitted files are the shapes
# the khursani campaign carried (or lacked).
S103W2_GREP_TARGETS = (
    ".rumpun/rumpun.yaml",
    ".rumpun/seasons/s1.yaml",
    ".rumpun/seasons/_template.yaml",
    ".rumpun/seasons/_competition.yaml",
    "tools/artifact_check.py",
)


def _s103w2_repo() -> Path:
    """Repo root: the first ancestor of this file holding pyproject.toml."""
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s103w2_ruff() -> str:
    """The ruff binary: repo .venv, then ~/.local/bin, then PATH; else fail."""
    repo = _s103w2_repo()
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


def _s103w2_run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """One bounded subprocess; a timeout is a pin failure, not a hang."""
    try:
        return subprocess.run(
            argv, cwd=str(cwd), capture_output=True, text=True, timeout=S103W2_TIMEOUT
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"{' '.join(argv[1:4])} exceeded {S103W2_TIMEOUT}s"
        raise AssertionError(msg) from exc


def _s103w2_snapshot(root: Path) -> dict[str, bytes]:
    """Byte snapshot of every file under root, keyed by relative posix path."""
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def _s103w2_emitted_tree(tmp_path: Any) -> Path:
    """A fresh scaffolded campaign via in-process init; returns the target."""
    target = tmp_path / "camp"
    scaffold.init_project(target)
    return target


def test_s103w2_emitted_tree_has_zero_singular_agent_keys(tmp_path: Any) -> None:
    """Grep-shape over every emitted file: zero singular `agent:` keys.

    The khursani evaluate phase carried `agent: judge`; init must never emit
    that shape again -- not in the seasons, the prompts, the config, and not
    in the shipped checker either. Two greps bind: the YAML key shape (block
    or list-item, any indent) over every file, and the raw substring over the
    .yaml files, where `agent:` is always a key attempt (flow style included).
    The walk is non-vacuous: the five khursani-shaped files must exist.
    """
    target = _s103w2_emitted_tree(tmp_path)
    for rel in S103W2_GREP_TARGETS:
        assert (target / rel).is_file(), f"emitted tree lacks {rel}"
    offenders: list[str] = []
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), start=1):
            if S103W2_SINGULAR_AGENT.match(line):
                offenders.append(f"{path.relative_to(target)}:{i}: {line.strip()}")
        if path.suffix in (".yaml", ".yml") and "agent:" in text:
            offenders.append(f"{path.relative_to(target)}: raw substring agent:")
    assert not offenders, (
        "singular agent: keys in the emitted tree:\n" + "\n".join(offenders)
    )


def test_s103w2_emitted_checker_is_byte_real(tmp_path: Any) -> None:
    """The shipped checker exists, is byte-identical to source, passes ruff."""
    target = _s103w2_emitted_tree(tmp_path)
    shipped = target / "tools" / "artifact_check.py"
    assert shipped.is_file(), "init shipped no checker (the khursani tools/ absence)"
    source = _s103w2_repo() / "tools" / "artifact_check.py"
    assert source.is_file(), f"source checker missing: {source}"
    assert shipped.read_bytes() == source.read_bytes(), (
        "shipped checker differs from the source tree's checker"
    )
    ruff = _s103w2_ruff()
    lint = _s103w2_run(target, [ruff, "check", "--no-respect-gitignore", str(shipped)])
    assert lint.returncode == 0, f"ruff rc={lint.returncode}: {lint.stdout}{lint.stderr}"


def test_s103w2_sourceless_tree_raises_structurally(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hidden source tree: the walk-up refuses, init writes nothing.

    The source tree is hidden by pointing the module __file__ at an isolated
    fake tree under tmp_path -- the real tools/artifact_check.py is never
    moved or renamed, and monkeypatch restores on any exit. Positive control
    first: unpatched, the walk-up finds the real checker.
    """
    source = _s103w2_repo() / "tools" / "artifact_check.py"
    assert scaffold._checker_source() == source, "positive control: walk-up lost"
    fake_pkg = tmp_path / "site-packages" / "rumpun"
    fake_pkg.mkdir(parents=True)
    for ancestor in [*fake_pkg.parents, fake_pkg]:
        assert not (ancestor / "tools" / "artifact_check.py").exists(), (
            f"isolation broken: {ancestor} holds a checker"
        )
    monkeypatch.setattr(scaffold, "__file__", str(fake_pkg / "scaffold.py"))
    with pytest.raises(scaffold.ScaffoldError, match="tools/artifact_check\\.py"):
        scaffold._checker_source()
    target = tmp_path / "camp"
    with pytest.raises(scaffold.ScaffoldError, match="tools/artifact_check\\.py"):
        scaffold.init_project(target)
    assert not target.exists(), "init wrote despite the structural refusal"


def test_s103w2_reinit_refuses_and_writes_nothing(tmp_path: Any) -> None:
    """Re-init into a scaffolded campaign refuses; the tree is byte-unchanged."""
    target = _s103w2_emitted_tree(tmp_path)
    before = _s103w2_snapshot(target)
    with pytest.raises(scaffold.ScaffoldError, match="refuses to overwrite"):
        scaffold.init_project(target)
    assert _s103w2_snapshot(target) == before, "the refused re-init changed the tree"


def test_s103w2_existing_checker_destination_refuses(tmp_path: Any) -> None:
    """A pre-existing checker dest is refused; its sentinel bytes survive.

    The dest guard sits after the .rumpun writes and before the copyfile, so
    the refused init leaves the .rumpun tree behind -- pinned as current
    behavior; the binding claim is the destination file itself: never copied
    over, sentinel bytes intact.
    """
    target = tmp_path / "camp"
    dest = target / "tools" / "artifact_check.py"
    dest.parent.mkdir(parents=True)
    sentinel = b"# s103w2 sentinel: init must refuse this file, never copy over it\n"
    dest.write_bytes(sentinel)
    with pytest.raises(
        scaffold.ScaffoldError, match="refusing to overwrite existing file"
    ):
        scaffold.init_project(target)
    assert dest.read_bytes() == sentinel, "the existing checker dest was overwritten"
