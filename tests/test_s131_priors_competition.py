"""s131 w2 pins: the pack teaches the competition season.

Landed by w2, budget-terminated mid-edit, rewritten by the close
worker from the lane's brief: the real pack lints clean with the
competition prior, the registry digest equals the recomputed tree
digest (the close-check equality), and the template names the three
owed things. Reads only; no installs; no network.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from rumpun import plugin, yamlio


def _repo() -> Path:
    """The repo root, by pyproject walk-up (the s120 precedent)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


REPO = _repo()
PACK = REPO / ".rumpun" / "plugins" / "kancil-base"
REGISTRY = REPO / ".rumpun" / "plugins.yml"
PRIOR = PACK / "priors" / "competition-season.md"

_OWED = ("external outcome", "named baseline", "unmeasured")


def test_real_pack_lints_clean_with_competition_prior() -> None:
    """The manifest loads strict and the priors carry no season ids."""
    manifest = plugin.load_manifest(PACK)
    assert isinstance(manifest, dict), "the manifest did not load strict"
    text = PRIOR.read_text(encoding="utf-8")
    assert not re.search(r"\bs\d+\b", text), "the prior carries a season id"


def test_registry_digest_equals_recomputed_tree() -> None:
    """The close-check equality, pinned at test time (the s120 shape)."""
    claimed = yamlio.load(REGISTRY)["plugins"]["kancil-base"]["digest"]
    actual = plugin.priors_digest(PACK)
    assert claimed == actual, (
        f"registry digest {claimed} != recomputed {actual}: "
        "the reseal did not land or a sibling moved the manifest"
    )


@pytest.mark.parametrize("owed", _OWED)
def test_prior_names_the_owed_things(owed: str) -> None:
    """The prior names the external outcome, the baseline, the note."""
    text = PRIOR.read_text(encoding="utf-8")
    assert owed in text, f"the prior never names {owed!r}"
