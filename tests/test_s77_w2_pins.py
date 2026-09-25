"""s77 w2 pins — the kancil version seam's offline-verifiable contract.

Spec source: .rumpun/runs/s77/w2/prompt.md (the s77 w2 brief). The w1
lane distills the real skills prompt into the kancil-base pack; these
pins hold the version-tracking contract offline over fixture packs: no
route call, no uv call, no pack mutation, no .rumpun state edits.

Contract these pins hold -- src/rumpun/skills.py + src/rumpun/kanban.py:

1. skills_version(pack_dir): the kancil-version frontmatter of the
   pack's priors/skills/kancil-*-skills.md, as a stripped string; None
   when the file, the --- fence, or the key is absent. Unparsable
   frontmatter raises SkillsError naming the file, never a silent skip.
2. installed_kancil_version(): the s82 w2 rewire reads the route
   binary first; these pins hold importlib.metadata as the
   binary-absent fallback, against the live metadata read and a
   monkeypatched not-installed environment.
3. version_aligned(pack_dir), the alignment matrix: equal -> True;
   prompt-newer and installed-newer -> False; either side unknown ->
   None (never confused with a mismatch).
4. kanban._skills_cards via kanban.render: with the pack installed
   (manifest.yaml, the install record per plugin.py), exactly the
   known-mismatch arm cards -- the title names both versions, the seq 8
   four sentences follow, the body names the re-align command
   `uv tool install --force /mnt/data/work/kancil` -- in NEED HUMAN.
   Aligned (True), unknown (None), and pack-absent render no card; the
   prompt's "falsy" arm reads as False (recorded in notes.md).
5. The s69 degrade holds: pickup raising, render still renders the
   local columns with the skills card up.
"""

from __future__ import annotations

import importlib.metadata
import logging
from pathlib import Path

import pytest

from rumpun import kanban, skills

logger = logging.getLogger(__name__)

S77W2_MANIFEST = "name: kancil-base\nversion: 0.1.0\ndigest: " + "0" * 64 + "\n"


def _s77w2_campaign(tmp_path: Path, name: str = "s77w2camp") -> Path:
    """A fresh .rumpun root: seasons, ledger, runs, no budget cap."""
    root = tmp_path / name / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        "autonomy:\n  stage: manual\n", encoding="utf-8"
    )
    return root


def _s77w2_pack(root: Path, skills_text: str | None) -> Path:
    """Install the kancil-base fixture pack; None text = no skills file."""
    pack = root / "plugins" / "kancil-base"
    (pack / "priors" / "skills").mkdir(parents=True, exist_ok=True)
    (pack / "manifest.yaml").write_text(S77W2_MANIFEST, encoding="utf-8")
    if skills_text is not None:
        (pack / "priors" / "skills" / "kancil-2.2-skills.md").write_text(
            skills_text, encoding="utf-8"
        )
    return pack


def _s77w2_versioned(version: str) -> str:
    return (
        f"---\nkancil-version: {version}\nsource-commit: s77w2fixture\n---\n"
        "the writer-facing operating prompt\n"
    )


def _s77w2_patch_install(monkeypatch: pytest.MonkeyPatch, version: str | None) -> None:
    """Pin the installed side through importlib.metadata, the real seam."""
    real = importlib.metadata.version

    def fake(distribution):
        if distribution == "kancil":
            if version is None:
                raise importlib.metadata.PackageNotFoundError(distribution)
            return version
        return real(distribution)

    monkeypatch.setattr(importlib.metadata, "version", fake)
    # s82 w2: the binary-first rewire keeps this metadata seam reachable
    # by pinning the route binary absent.
    monkeypatch.setattr(skills, "_resolve_kancil_binary", lambda: None)


def _s77w2_patch_pickup(monkeypatch: pytest.MonkeyPatch, raise_: bool = False) -> None:
    """Patch both seam names (the s69 'either import style lands' rule)."""
    from rumpun import board

    def seam(*args: object, **kwargs: object) -> list[dict[str, str]]:
        if raise_:
            raise RuntimeError("s77w2: board pickup exploded")
        return []

    monkeypatch.setattr(board, "pickup", seam)
    if hasattr(kanban, "pickup"):
        monkeypatch.setattr(kanban, "pickup", seam)


def test_s77w2_skills_version_reads_frontmatter(tmp_path: Path) -> None:
    """The frontmatter kancil-version reads back as a stripped string."""
    pack = _s77w2_pack(_s77w2_campaign(tmp_path), _s77w2_versioned("2.2.5"))
    assert skills.skills_version(pack) == "2.2.5"


def test_s77w2_skills_version_none_when_absent(tmp_path: Path) -> None:
    """No file, no --- fence, no key: each absent arm reads None."""
    no_file = _s77w2_pack(_s77w2_campaign(tmp_path), None)
    assert skills.skills_version(no_file) is None, "no skills file: not None"
    unfenced = _s77w2_pack(
        _s77w2_campaign(tmp_path, name="s77w2nofence"), "plain prose, no fence\n"
    )
    assert skills.skills_version(unfenced) is None, "no fence: not None"
    keyless = _s77w2_pack(
        _s77w2_campaign(tmp_path, name="s77w2nokey"),
        "---\nsource-commit: x\n---\nprompt\n",
    )
    assert skills.skills_version(keyless) is None, "no key: not None"


def test_s77w2_skills_version_refuses_unparsable_frontmatter(tmp_path: Path) -> None:
    """Unparsable frontmatter is a loud SkillsError naming the file."""
    pack = _s77w2_pack(
        _s77w2_campaign(tmp_path), "---\nkancil-version: [unclosed\n---\nbody\n"
    )
    with pytest.raises(skills.SkillsError, match="skills"):
        skills.skills_version(pack)


def test_s77w2_installed_version_matches_live_metadata() -> None:
    """The live read follows the s82 surface: the route binary when present.

    Held against the live machine, not a fixture: with a kancil binary
    on PATH the read is its probe's version line (the isolated tool
    env's dist-info); absent, it is importlib.metadata's answer or
    None. The pre-s82 premise -- live read == rumpun-env metadata --
    was the issue #8 defect.
    """
    if skills._resolve_kancil_binary() is not None:
        live = skills.installed_kancil_version()
        assert isinstance(live, str) and live, (
            f"a present route binary must probe to a version, got {live!r}"
        )
        return
    try:
        expected = importlib.metadata.version("kancil")
    except importlib.metadata.PackageNotFoundError:
        expected = None
    assert skills.installed_kancil_version() == expected


def test_s77w2_installed_version_none_when_not_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A not-installed kancil reads None, never a raise."""
    _s77w2_patch_install(monkeypatch, None)
    assert skills.installed_kancil_version() is None


def test_s77w2_alignment_matrix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """equal -> True; prompt-newer and installed-newer -> False."""
    equal = _s77w2_pack(_s77w2_campaign(tmp_path), _s77w2_versioned("2.2.5"))
    _s77w2_patch_install(monkeypatch, "2.2.5")
    assert skills.version_aligned(equal) is True
    newer_pack = _s77w2_pack(
        _s77w2_campaign(tmp_path, name="s77w2pn"), _s77w2_versioned("2.3.0")
    )
    assert skills.version_aligned(newer_pack) is False, "prompt-newer must mismatch"
    newer_installed = _s77w2_pack(
        _s77w2_campaign(tmp_path, name="s77w2in"), _s77w2_versioned("2.2.5")
    )
    _s77w2_patch_install(monkeypatch, "2.2.6")
    assert skills.version_aligned(newer_installed) is False, "installed-newer must mismatch"


def test_s77w2_alignment_none_when_either_side_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Either side unknown reads None, never a mismatch."""
    _s77w2_patch_install(monkeypatch, "2.2.5")
    keyless = _s77w2_pack(
        _s77w2_campaign(tmp_path, name="s77w2nokey"),
        "---\nsource-commit: x\n---\nprompt\n",
    )
    assert skills.version_aligned(keyless) is None, "unknown prompt side is not None"
    _s77w2_patch_install(monkeypatch, None)
    versioned = _s77w2_pack(
        _s77w2_campaign(tmp_path, name="s77w2noinst"), _s77w2_versioned("2.2.5")
    )
    assert skills.version_aligned(versioned) is None, "unknown installed side is not None"


def test_s77w2_mismatch_cards_once_with_four_sentences(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A known mismatch: one card, both versions, four sentences."""
    root = _s77w2_campaign(tmp_path)
    _s77w2_pack(root, _s77w2_versioned("2.2.5"))
    _s77w2_patch_install(monkeypatch, "2.2.6")
    _s77w2_patch_pickup(monkeypatch)
    cards = kanban._skills_cards(root)
    assert len(cards) == 5, f"title plus four sentences expected: {cards!r}"
    assert cards[0] == (
        "- kancil version drift: skills prompt 2.2.5, installed kancil 2.2.6"
        "  [plugins/kancil-base priors frontmatter]"
    ), f"the title must name both versions: {cards[0]!r}"
    assert cards[1].startswith(
        "    what happened: the installed pack's skills prompt"
    ), cards[1]
    assert "kancil 2.2.5" in cards[1] and "2.2.6" in cards[1], cards[1]
    assert cards[2].startswith("    what needs doing: re-align one side"), cards[2]
    assert "uv tool install --force /mnt/data/work/kancil" in cards[2], cards[2]
    assert cards[3].startswith("    why it needs a human:"), cards[3]
    assert cards[4].startswith("    what happens if nobody acts:"), cards[4]
    rendered = kanban.render(root)
    need_at = rendered.index("NEED HUMAN")
    done_at = rendered.index("\nDONE ")
    card_at = rendered.index("- kancil version drift:")
    assert need_at < card_at < done_at, "the card is not in the NEED HUMAN column"


def test_s77w2_aligned_unknown_and_packless_render_no_card(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Aligned (True), unknown (None), pack-absent: each renders no card."""
    root = _s77w2_campaign(tmp_path)
    _s77w2_pack(root, _s77w2_versioned("2.2.5"))
    _s77w2_patch_install(monkeypatch, "2.2.5")
    _s77w2_patch_pickup(monkeypatch)
    assert kanban._skills_cards(root) == [], "an aligned install must not card"
    assert "kancil version drift" not in kanban.render(root), "aligned leaked a card"
    unknown = _s77w2_campaign(tmp_path, name="s77w2unk")
    _s77w2_pack(unknown, "---\nsource-commit: x\n---\nprompt\n")
    assert kanban._skills_cards(unknown) == [], "an unknown side must not card"
    packless = _s77w2_campaign(tmp_path, name="s77w2packless")
    assert kanban._skills_cards(packless) == [], "a packless campaign must not card"


def test_s77w2_pickup_raise_degrades_with_the_skills_card_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The s69 seam holds: pickup raising, the skills card stays up."""
    root = _s77w2_campaign(tmp_path)
    _s77w2_pack(root, _s77w2_versioned("2.2.5"))
    _s77w2_patch_install(monkeypatch, "2.2.6")
    _s77w2_patch_pickup(monkeypatch, raise_=True)
    rendered = kanban.render(root)
    assert (
        "- kancil version drift: skills prompt 2.2.5, installed kancil 2.2.6" in rendered
    ), "the skills card dropped under degradation"
    assert "campaign_cost_cap is unset" in rendered, "the local NEED HUMAN column dropped"
