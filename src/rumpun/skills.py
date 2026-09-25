"""rumpun skills — the kancil version seam (s77 w2; s82 w2 rewires the installed side).

A pack's skills prompt describes one kancil version; the machine runs
whatever kancil the route actually executes. This module is the read
side of that comparison: the prompt's frontmatter version, the
installed version, and their alignment. The installed side reads the
ROUTE executable (s82 w2, issue #8): the kancil binary on PATH -- the
exact file the `kancil loop` route spawns -- probed by a bounded
subprocess; rumpun's own importlib.metadata answers only when the
binary is absent. No network, no writes -- kanban's _skills_cards
turns a known mismatch into a NEED HUMAN card; nothing here cards by
itself.
"""

from __future__ import annotations

import importlib.metadata
import logging
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

SKILLS_VERSION_KEY = "kancil-version"

# s82 w2 (issue #8): the installed side reads the ROUTE executable --
# the kancil binary on PATH, the exact file the `kancil loop` route
# spawns. kancil 2.2.5 has no self-reporting --version (the source
# sweep), so the resolved console script's own interpreter runs the
# dist-info probe of the isolated tool env. _TOOL_ENV_PROBE is a pin
# seam; the parse is line-anchored, prose is garbage.
KANCIL_BINARY = "kancil"
VERSION_PROBE_TIMEOUT_S = 10.0
_TOOL_ENV_PROBE = "from importlib.metadata import version; print(version('kancil'))"
_VERSION_LINE_RE = re.compile(
    r"(?mi)^[ \t]*(?:kancil[ \t]+)?v?(?P<version>\d+(?:\.\d+)+[^\s]*)[ \t]*$"
)
VersionRunner = Callable[[str], str]


class SkillsError(Exception):
    """A skills file exists but its frontmatter is unreadable."""


def skills_version(pack_dir: Path) -> str | None:
    """The kancil-version frontmatter of the pack's skills file.

    Pure read. The skills file is the kancil-*-skills.md under the
    pack's priors/skills/ (lexically first when several). None when
    the file, the frontmatter fence, or the key is absent. Unparsable
    frontmatter raises SkillsError naming the file, never a silent
    skip.
    """
    pack_dir = Path(pack_dir)
    matches = sorted((pack_dir / "priors" / "skills").glob("kancil-*-skills.md"))
    if not matches:
        return None
    path = matches[0]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        msg = f"{path}: unreadable skills file: {exc}"
        raise SkillsError(msg) from exc
    front = _frontmatter(text)
    if front is None:
        return None
    try:
        data = yaml.safe_load(front)
    except yaml.YAMLError as exc:
        msg = f"{path}: unparsable frontmatter: {exc}"
        raise SkillsError(msg) from exc
    if not isinstance(data, dict):
        return None
    version = data.get(SKILLS_VERSION_KEY)
    if version is None:
        return None
    logger.debug("skills prompt %s carries %s %s", path, SKILLS_VERSION_KEY, version)
    return str(version).strip()


def _frontmatter(text: str) -> str | None:
    """The YAML between a leading --- fence; None when unfenced."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for end in range(1, len(lines)):
        if lines[end].strip() == "---":
            return "\n".join(lines[1:end])
    return None


def _resolve_kancil_binary() -> str | None:
    """The kancil binary on PATH -- the exact file the route spawns.

    The kancil route runs the unqualified `kancil` (rumpun.yaml), so
    PATH resolution is the route's own resolution. None when absent,
    which arms the importlib.metadata fallback.
    """
    return shutil.which(KANCIL_BINARY)


def _metadata_version() -> str | None:
    """rumpun's importlib.metadata answer; the binary-absent fallback.

    PackageNotFoundError -> None; any other metadata error propagates:
    an unreadable environment is not "not installed". Reading this env
    while the route runs an isolated tool install is the issue #8
    defect, so it answers only when no binary is on PATH.
    """
    try:
        return importlib.metadata.version("kancil")
    except importlib.metadata.PackageNotFoundError:
        return None


def _parse_version_output(text: str) -> str | None:
    """The version line in probe output; None when none (garbage in)."""
    for match in _VERSION_LINE_RE.finditer(text):
        return match.group("version")
    return None


def _default_version_runner(binary: str) -> str:
    """The bounded probe: the binary's own interpreter reports the version.

    Resolves the console script (uv symlinks ~/.local/bin/kancil into
    the tool env), reads its shebang interpreter, and runs the
    dist-info probe through it -- a bounded subprocess
    (VERSION_PROBE_TIMEOUT_S), offline, no writes. Returns stdout;
    every other outcome is garbage the caller reads as None.
    """
    real = Path(binary).resolve()
    try:
        with real.open("rb") as fh:
            first = fh.readline().decode("ascii", errors="replace")
    except OSError:
        return ""
    if not first.startswith("#!"):
        return ""
    return subprocess.run(
        [first[2:].strip(), "-c", _TOOL_ENV_PROBE],
        capture_output=True,
        text=True,
        timeout=VERSION_PROBE_TIMEOUT_S,
        check=False,
    ).stdout


def installed_kancil_version(runner: VersionRunner | None = None) -> str | None:
    """The route binary's kancil version; None when unknown or absent.

    The resolved kancil binary is probed through `runner` (default:
    _default_version_runner, a bounded subprocess) and the output is
    parsed: unparsable output is None, never a fallback. `runner`
    raising OSError or a subprocess error -- a hung or unspawnable
    probe -- is None, logged, never a fallback. rumpun's
    importlib.metadata answers only when the binary is ABSENT: reading
    rumpun's env while the route runs an isolated tool install is the
    issue #8 defect.
    """
    binary = _resolve_kancil_binary()
    if binary is None:
        return _metadata_version()
    try:
        output = (runner or _default_version_runner)(binary)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning(
            "kancil version probe failed (%s); the installed side reads unknown",
            exc,
        )
        return None
    return _parse_version_output(output)


def version_aligned(pack_dir: Path, runner: VersionRunner | None = None) -> bool | None:
    """True when the prompt's kancil-version equals the route binary's.

    False when both sides are known and differ, either direction
    (prompt newer or binary newer). None when either side is unknown
    -- no frontmatter version, no binary and no metadata, or garbage
    probe output -- so a caller never mistakes an unknown for a
    mismatch. `runner` passes through to the installed-side probe.
    """
    prompt = skills_version(pack_dir)
    installed = installed_kancil_version(runner=runner)
    if prompt is None or installed is None:
        return None
    return prompt == installed
