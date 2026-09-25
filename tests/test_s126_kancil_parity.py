"""s126 w2 pins — the kancil-base pack vs the installed kancil CLI parity.

Spec-first pins (red against current code) for the s126 w2 contract: the
kancil-base plugin may legitimately trail the installed kancil CLI, but
nothing may silently drift: on drift the pin fails naming both versions,
and the upgrade is the operator's call. Measured 2026-09-20: the pack
manifest declares 0.1.0, the installed kancil is 2.2.6, and the CLI
carries no version verb or flag (both `kancil version` and
`kancil --version` exit 2 with argparse usage text), so the installed
version reads from the kancil dist-info under the uv tools dir. Spec and
measured red set: .rumpun/runs/s126/w2/notes.md.

Fixture discipline: reads only. No installs, no network. The CLI version
comes from installed dist-info; the pack version from the installed pack
manifest via the existing strict loader (plugin.load_manifest).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from rumpun import plugin

_DOTTED = re.compile(r"^\d+(\.\d+)+$")


def _s126w2_repo() -> Path:
    """The repo root: the first pyproject.toml walking up from this file."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def test_pack_version_reads_manifest() -> None:
    """The pack-side seam reads the installed kancil-base manifest."""
    version = plugin.read_pack_version(_s126w2_repo())
    assert _DOTTED.match(version), version


def test_cli_version_reads_installed() -> None:
    """The CLI-side seam reads the installed kancil dist-info version."""
    version = plugin.read_kancil_cli_version()
    assert _DOTTED.match(version), version


@pytest.mark.xfail(
    reason="kancil-base pack 0.1.0 trails the installed CLI 2.2.6; the "
    "upgrade is the operator's call (reclassified at the s126 close: "
    "strict so an upgrade flips this to a failure and forces promotion)",
    strict=True,
)
def test_kancil_base_parity() -> None:
    """The parity pin: pass on equality; on drift, name both versions.

    Landed as a standing hard red; reclassified at the s126 close to a
    strict xfail - the drift stays named, the suite stays green, and an
    upgrade flips this to a failure that forces promotion to a pass.
    """
    pack_version = plugin.read_pack_version(_s126w2_repo())
    cli_version = plugin.read_kancil_cli_version()
    assert pack_version == cli_version, (
        f"kancil-base pack {pack_version} != installed kancil CLI {cli_version}: "
        "the plugin trails the CLI and the gap is now named; "
        "the upgrade is the operator's call"
    )
