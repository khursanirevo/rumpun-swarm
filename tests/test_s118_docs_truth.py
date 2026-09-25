"""s118 docs-truth pins -- the changelog states the version truth.

Spec source: the s118 w2 brief (the outcome-anchor lane) and the
season-close protocol's step 6: bump the package version and move
[Unreleased] into the dated section. The clause was skipped all
segment; the changelog's newest dated section sat at 0.14.0 while
pyproject.toml climbed to 0.23.0. The rule this pin lands: the
changelog's newest dated section names the current package version.
While the two diverge the pin fails loudly, at every close, until
the dated sections exist. The README carries no version literal of
its own: its Version section names pyproject.toml as the authority,
so that file cannot go stale either.

Offline: reads only committed repo files (CHANGELOG.md, README.md,
pyproject.toml) located by walking up from this file to the
pyproject.toml at the repo root; nothing runs, nothing writes, no
campaign state is touched.

Grafting: drop this file into tests/. Helpers and constants carry
the _s118 prefix; nothing collides with existing defs.
"""

from __future__ import annotations

import re
from itertools import pairwise
from pathlib import Path

_S118_TESTS_DIR = Path(__file__).resolve().parent


def _s118_repo_file(name: str) -> Path:
    """Walk up from this test file to the repo root holding pyproject.toml.

    The checker's archive extract carries no .git and no .venv; the
    walk-up keys on the committed pyproject.toml only.
    """
    for candidate in [_S118_TESTS_DIR.parent, *_S118_TESTS_DIR.parent.parents]:
        if (candidate / "pyproject.toml").is_file():
            return candidate / name
    raise AssertionError("no pyproject.toml above tests/: not the repo root")


def _s118_read(name: str) -> str:
    path = _s118_repo_file(name)
    assert path.is_file(), f"the repo file is missing: {path}"
    return path.read_text(encoding="utf-8")


_S118_DATED = re.compile(r"^## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})\s*$", re.M)


def _s118_dated_versions() -> list[tuple[int, int, int]]:
    """The changelog's dated sections as semver tuples, newest first."""
    text = _s118_read("CHANGELOG.md")
    versions = []
    for version, _date in _S118_DATED.findall(text):
        major, minor, patch = (int(part) for part in version.split("."))
        versions.append((major, minor, patch))
    return versions


def _s118_pyproject_version() -> str:
    text = _s118_read("pyproject.toml")
    match = re.search(r'^version = "([^"]+)"', text, re.M)
    assert match, "pyproject.toml carries no version line"
    return match.group(1)


def test_s118_pin1_newest_dated_section_is_the_package_version() -> None:
    """Red-first: the changelog's newest dated section names pyproject's version.

    The skipped close-protocol clause, made enforceable: while the newest
    dated section trails pyproject.toml, the suite stays red and the close
    cannot call itself done.
    """
    newest = _s118_dated_versions()
    assert newest, "CHANGELOG.md holds no dated section at all"
    current = _s118_pyproject_version()
    major, minor, patch = (int(part) for part in current.split("."))
    assert newest[0] == (major, minor, patch), (
        f"the changelog's newest dated section {newest[0]} diverges from "
        f"pyproject.toml's version {current} - run the close protocol's "
        "step 6: move [Unreleased] into a dated section"
    )


def test_s118_pin2_dated_sections_descend() -> None:
    """Green guard: dated sections run newest first, strictly descending.

    Keep-a-Changelog order; the s96 out-of-order close must not tempt a
    newer section below an older one.
    """
    versions = _s118_dated_versions()
    assert versions, "CHANGELOG.md holds no dated section at all"
    assert all(
        newer > older for newer, older in pairwise(versions)
    ), f"dated sections are not strictly newest-first: {versions}"


def test_s118_pin3_readme_names_no_version_literal() -> None:
    """Red-first: the README's Version section names pyproject as authority.

    The section claimed 0.11.0 while pyproject climbed; a version literal
    in the section goes stale at every close. The section carries the rule
    instead of a number, and the pin fails while any N.N.N literal sits
    in it.
    """
    text = _s118_read("README.md")
    match = re.search(r"^## Version\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert match, "README.md carries no ## Version section"
    section = match.group(1)
    literals = re.findall(r"\d+\.\d+\.\d+", section)
    assert not literals, (
        f"the README Version section hardcodes version literals {literals} "
        "- it must name pyproject.toml as the authority instead"
    )
    assert "pyproject.toml" in section, (
        "the README Version section must name pyproject.toml as the version "
        "authority"
    )
