"""s111 w2 pins — the composer's fourth render: pack digest equality.

The composer clause has ridden briefs since s103 without landing as a
deliverable. This pin lands it: render a pack over a fixture pack dir
(manifest seal + priors digest) and assert the equality the close
check's DIGESTS pass enforces: the claimed digest equals the recomputed
one, and a mutated prior moves the digest so drift reads DELTA.

Spec sources: the brief (.rumpun/runs/s111/w2/prompt.md), the close
check (tools/artifact_check.py: recompute_pack_digest + digest_packs),
and the s46w2 pinned digest convention: sha256 over the pack's priors/
tree in sorted pack-relative POSIX-path order, updating rel path, NUL,
then bytes, no trailing separator; empty or missing priors/ hashes as
sha256 of empty input.

Red-first: the seal-equality pins first ran against a fixture sealed
with STALE (below) and failed on `claimed != recomputed` — the exact
DELTA condition the close check enforces. The fix was the true seal,
not a code change; plugin.py needed no seam.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from rumpun import plugin

# A stale claim as a digest: the DELTA condition as a value. The
# red-first run sealed the fixture with this and watched the pins fail.
STALE = "0" * 64


def _s111w2_priors_digest(pack: Path) -> str:
    """The digest convention, computed independently of rumpun.plugin.
    Mirrors tools/artifact_check.py recompute_pack_digest: sha256 over
    the pack's priors/ files in sorted pack-relative POSIX-path order,
    updating rel path, NUL, then bytes; no trailing separator; a missing
    priors/ hashes as sha256 of empty input."""
    digest = hashlib.sha256()
    priors = pack / "priors"
    if priors.is_dir():
        for path in sorted(p for p in priors.rglob("*") if p.is_file()):
            digest.update(path.relative_to(pack).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _s111w2_pack(pack: Path, *, digest_override: str | None = None) -> None:
    """Write a fixture pack into pack/: a priors/ tree plus manifest.yaml
    sealed with the pack's true digest. The red-first run sealed STALE
    instead (digest_override=STALE) to force the DELTA condition."""
    (pack / "priors" / "patterns").mkdir(parents=True, exist_ok=True)
    (pack / "priors" / "patterns" / "baseline.md").write_text(
        "Start from a fast, complete baseline before tuning anything.\n",
        encoding="utf-8",
    )
    (pack / "priors" / "templates").mkdir(parents=True, exist_ok=True)
    (pack / "priors" / "templates" / "execute.md").write_text(
        "# Execute\n\nRun the assigned experiments exactly as committed.\n",
        encoding="utf-8",
    )
    digest = digest_override or plugin.priors_digest(pack)
    (pack / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "composer-base",
                "version": "0.1.0",
                "digest": digest,
                "source": "the s111 fixture pack (the composer render)",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _s111w2_registry(root: Path, name: str, digest: str) -> Path:
    """A plugins.yml in the close-check layout; returns the registry path."""
    reg_dir = root / ".rumpun"
    reg_dir.mkdir(parents=True, exist_ok=True)
    reg_path = reg_dir / "plugins.yml"
    reg_path.write_text(
        yaml.safe_dump(
            {
                "plugins": {
                    name: {
                        "version": "0.1.0",
                        "digest": digest,
                        "installed_at": 1789684985.4152308,
                        "source": "the campaign's proven gates and patterns",
                    }
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return reg_path


def test_seal_equals_recompute(tmp_path: Any) -> None:
    """The composer render: the manifest's claimed digest equals the
    recomputed one, via the seam and via the independent mirror."""
    pack = tmp_path / "composer-base"
    _s111w2_pack(pack)
    claim = yaml.safe_load((pack / "manifest.yaml").read_text(encoding="utf-8"))[
        "digest"
    ]
    seam = plugin.priors_digest(pack)
    mirror = _s111w2_priors_digest(pack)
    assert claim == seam, f"claimed != recomputed (seam): {claim} vs {seam}"
    assert seam == mirror, f"seam != independent mirror: {seam} vs {mirror}"


def test_mutated_prior_moves_digest(tmp_path: Any) -> None:
    """A mutated prior moves the digest: the sealed claim stops matching,
    so the close check would read DELTA."""
    pack = tmp_path / "composer-base"
    _s111w2_pack(pack)
    claim = yaml.safe_load((pack / "manifest.yaml").read_text(encoding="utf-8"))[
        "digest"
    ]
    seam0 = plugin.priors_digest(pack)
    assert claim == seam0, f"pre-mutation: claimed != recomputed: {claim} vs {seam0}"
    with (pack / "priors" / "patterns" / "baseline.md").open(
        "a", encoding="utf-8"
    ) as fh:
        fh.write("mutated\n")
    seam1 = plugin.priors_digest(pack)
    mirror1 = _s111w2_priors_digest(pack)
    assert seam1 != seam0, "mutated prior left the digest unchanged"
    assert seam1 == mirror1, "seam != independent mirror after mutation"
    assert claim != seam1, "stale claim matched the mutated tree; drift unseen"


def test_registry_match_then_delta(tmp_path: Any) -> None:
    """The close check's read, mirrored on the installed layout: the
    registry claim over root/.rumpun/plugins/<name> reads MATCH on the
    true seal and DELTA after a prior mutates; the registry stays
    untouched. Loads the claim with the real registry reader."""
    root = tmp_path / "campaign"
    pack_dir = root / ".rumpun" / "plugins" / "composer-base"
    _s111w2_pack(pack_dir)
    sealed = yaml.safe_load((pack_dir / "manifest.yaml").read_text(encoding="utf-8"))[
        "digest"
    ]
    reg_path = _s111w2_registry(root, "composer-base", sealed)
    claimed = plugin._registry_load(reg_path)["composer-base"]["digest"]
    assert claimed == plugin.priors_digest(pack_dir), (
        f"claimed != recomputed (registry): {claimed} vs {plugin.priors_digest(pack_dir)}"
    )
    with (pack_dir / "priors" / "patterns" / "baseline.md").open(
        "a", encoding="utf-8"
    ) as fh:
        fh.write("mutated\n")
    claimed_again = plugin._registry_load(reg_path)["composer-base"]["digest"]
    recomputed = plugin.priors_digest(pack_dir)
    assert claimed_again != recomputed, "registry DELTA undetected after mutation"
    assert claimed_again == plugin._registry_load(reg_path)["composer-base"][
        "digest"
    ], "registry changed during the pin"
