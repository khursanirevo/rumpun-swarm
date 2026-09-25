"""s120 w2 pins — the priors refresh: real-pack lint and digest equality.

The kancil-base pack is the distilled knowledge other campaigns start
from. This refresh teaches it the conventions the ledger derived since
the pack last moved: the second-opinion rerun derivation, the notes
gate, the dissent marks. The pins:

1. plugin_lint over the real installed pack yields zero error findings
   (campaign-agnostic templates: no season ids, no absolute paths, no
   private-vocabulary tokens).
2. The registry claim in .rumpun/plugins.yml equals plugin.priors_digest
   over the real pack, the same equality the close check's DIGESTS pass
   enforces, pinned at test time.
3. Every top-level priors template carries the three sections the pack
   uses (The prior / Why this holds / How to apply).
"""

from __future__ import annotations

from pathlib import Path

from rumpun import plugin, yamlio


def _repo() -> Path:
    """The repo root, by pyproject walk-up (identical in the lane and in
    tests/, so the pin reads the same tree either way)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


REPO = _repo()
PACK = REPO / ".rumpun" / "plugins" / "kancil-base"
REGISTRY = REPO / ".rumpun" / "plugins.yml"


def test_real_pack_lints_clean() -> None:
    manifest = plugin.load_manifest(PACK)
    findings = plugin.plugin_lint(PACK, manifest)
    assert not findings, [f.message for f in findings]


def test_registry_digest_matches_recomputed() -> None:
    registry = yamlio.load(REGISTRY)
    claimed = registry["plugins"]["kancil-base"]["digest"]
    recomputed = plugin.priors_digest(PACK)
    assert claimed == recomputed, (
        f"registry claims {claimed} but priors recompute to {recomputed}: "
        "a priors edit moved the digest without the reseal"
    )


def test_toplevel_templates_carry_sections() -> None:
    sections = ("## The prior", "## Why this holds", "## How to apply")
    tops = sorted((PACK / "priors").glob("*.md"))
    assert len(tops) >= 6, f"expected the six top-level priors, got {len(tops)}"
    for path in tops:
        text = path.read_text(encoding="utf-8")
        for section in sections:
            assert section in text, f"{path.name}: missing section '{section}'"
