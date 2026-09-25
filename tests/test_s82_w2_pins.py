"""s82 w2 pins — the version surface reads the route binary (issue #8).

Spec source: .rumpun/runs/s82/w2/prompt.md (the s82 w2 brief) and issue
#8's required correction: the installed side reads the ROUTE
executable, not Python metadata in rumpun's environment. All pins are
offline: the probe is an injected runner or a patched probe constant
run against sys.executable; no real kancil call, no network, no pack
mutation, no .rumpun state edits.

Contract these pins hold -- src/rumpun/skills.py + src/rumpun/kanban.py:

1. installed_kancil_version(runner): the route binary's probe output
   parsed; garbage reads None; a raising probe reads None (logged).
2. fallback ordering: binary absent -> importlib.metadata; binary
   present -> metadata is never consulted, even on garbage probe
   output (reading rumpun's env while the route runs an isolated tool
   install is the issue #8 defect).
3. version_aligned + kanban._skills_cards: the issue #8 repro -- a
   pack stamped 0.0.0 against the binary's 2.2.5 -- reads alignment
   False and renders the NEED HUMAN card naming both versions; a
   garbage probe keeps the unknown arm (None, no card).
4. the alignment matrix keeps its three states under binary reads:
   equal -> True, either-newer -> False, either side unknown -> None.
5. _default_version_runner: the real bounded subprocess path offline --
   a fixture console script shebanged to sys.executable, probe patched
   -- runs and parses; a shebang-less file reads None.
"""

from __future__ import annotations

import importlib.metadata
import logging
import subprocess
import sys
from pathlib import Path

import pytest

from rumpun import kanban, skills

logger = logging.getLogger(__name__)

S82W2_MANIFEST = "name: kancil-base\nversion: 0.1.0\ndigest: " + "0" * 64 + "\n"

_CAMP = "autonomy:\n  stage: manual\n"


def _s82w2_campaign(tmp_path: Path, name: str = "s82w2camp") -> Path:
    """A fresh .rumpun root: seasons, ledger, runs, no budget cap."""
    root = tmp_path / name / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(_CAMP, encoding="utf-8")
    return root


def _s82w2_pack(root: Path, skills_text: str | None) -> Path:
    """Install the kancil-base fixture pack; None text = no skills file."""
    pack = root / "plugins" / "kancil-base"
    (pack / "priors" / "skills").mkdir(parents=True, exist_ok=True)
    (pack / "manifest.yaml").write_text(S82W2_MANIFEST, encoding="utf-8")
    if skills_text is not None:
        (pack / "priors" / "skills" / "kancil-2.2-skills.md").write_text(
            skills_text, encoding="utf-8"
        )
    return pack


def _s82w2_versioned(version: str) -> str:
    return (
        f"---\nkancil-version: {version}\nsource-commit: s82w2fixture\n---\n"
        "the writer-facing operating prompt\n"
    )


def _s82w2_fake_binary(
    tmp_path: Path, shebang: str = "#!/bin/sh\n", name: str = "s82w2-fake-kancil"
) -> str:
    """A fixture console script; shebang only, the probe is injected."""
    script = tmp_path / name
    script.write_text(shebang, encoding="utf-8")
    script.chmod(0o755)
    return str(script)


def _s82w2_patch_route_binary(
    monkeypatch: pytest.MonkeyPatch, path: str | None
) -> None:
    """Pin the route-binary resolution seam (_resolve_kancil_binary)."""
    monkeypatch.setattr(skills, "_resolve_kancil_binary", lambda: path)


def _s82w2_patch_metadata(monkeypatch: pytest.MonkeyPatch, version: str | None) -> None:
    """Pin rumpun-env importlib.metadata, the binary-absent fallback seam."""
    real = importlib.metadata.version

    def fake(distribution):
        if distribution == "kancil":
            if version is None:
                raise importlib.metadata.PackageNotFoundError(distribution)
            return version
        return real(distribution)

    monkeypatch.setattr(importlib.metadata, "version", fake)


def _s82w2_patch_pickup(monkeypatch: pytest.MonkeyPatch, raise_: bool = False) -> None:
    """Patch both seam names (the s69 'either import style lands' rule)."""
    from rumpun import board

    def seam(*args: object, **kwargs: object) -> list[dict[str, str]]:
        if raise_:
            raise RuntimeError("s82w2: board pickup exploded")
        return []

    monkeypatch.setattr(board, "pickup", seam)
    if hasattr(kanban, "pickup"):
        monkeypatch.setattr(kanban, "pickup", seam)


def test_s82w2_route_binary_output_parsed_garbage_reads_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The injected runner's output parsed; garbage reads None."""
    _s82w2_patch_route_binary(monkeypatch, "/s82w2/never-spawned")
    assert (
        skills.installed_kancil_version(runner=lambda _b: "2.2.5\n") == "2.2.5"
    ), "a bare version line must parse"
    assert (
        skills.installed_kancil_version(runner=lambda _b: "kancil 2.2.5\n") == "2.2.5"
    ), "an optional kancil prefix must parse"
    assert (
        skills.installed_kancil_version(runner=lambda _b: "v2.2.5\n") == "2.2.5"
    ), "an optional v prefix must parse"
    assert (
        skills.installed_kancil_version(runner=lambda _b: "bogus output, no version\n")
        is None
    ), "prose without a version line is garbage -> None"
    assert (
        skills.installed_kancil_version(runner=lambda _b: "") is None
    ), "empty probe output is garbage -> None"


def test_s82w2_runner_raising_probe_reads_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A raising probe is unknown (None), never a fallback, never a raise."""
    _s82w2_patch_route_binary(monkeypatch, "/s82w2/never-spawned")
    _s82w2_patch_metadata(monkeypatch, "9.9.9")
    def raising(_binary: str) -> str:
        raise subprocess.TimeoutExpired(cmd=["kancil"], timeout=1)

    assert (
        skills.installed_kancil_version(runner=raising) is None
    ), "a raising probe must read None, not the wrong env's metadata"


def test_s82w2_fallback_ordering_held_both_directions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Binary absent -> metadata; binary present -> metadata never consulted."""
    _s82w2_patch_route_binary(monkeypatch, None)
    _s82w2_patch_metadata(monkeypatch, "9.9.9")
    assert (
        skills.installed_kancil_version() == "9.9.9"
    ), "binary absent: the metadata fallback must answer"
    _s82w2_patch_route_binary(monkeypatch, "/s82w2/never-spawned")
    assert (
        skills.installed_kancil_version(runner=lambda _b: "2.2.5\n") == "2.2.5"
    ), "binary present: the binary's answer wins over metadata"
    assert (
        skills.installed_kancil_version(runner=lambda _b: "garbage\n") is None
    ), "binary present + garbage: None, never the wrong env's metadata"


def test_s82w2_default_runner_runs_the_probe_offline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The real runner: bounded subprocess against a fixture console script."""
    _s82w2_patch_route_binary(
        monkeypatch,
        _s82w2_fake_binary(tmp_path, "#!" + sys.executable + "\n"),
    )
    monkeypatch.setattr(skills, "_TOOL_ENV_PROBE", "print('2.2.5')")
    assert skills.installed_kancil_version() == "2.2.5", (
        "the default runner must run the shebang interpreter's probe"
    )
    _s82w2_patch_route_binary(
        monkeypatch,
        _s82w2_fake_binary(
            tmp_path, "plain text, no shebang\n", name="s82w2-no-shebang"
        ),
    )
    assert (
        skills.installed_kancil_version() is None
    ), "a shebang-less file reads None"
    _s82w2_patch_route_binary(
        monkeypatch,
        _s82w2_fake_binary(
            tmp_path, "#!/nonexistent/interp\n", name="s82w2-missing-interp"
        ),
    )
    assert (
        skills.installed_kancil_version() is None
    ), "an unspawnable interpreter reads None (OSError arm)"
    _s82w2_patch_route_binary(
        monkeypatch,
        _s82w2_fake_binary(
            tmp_path, "#!" + sys.executable + "\n", name="s82w2-pnf"
        ),
    )
    monkeypatch.setattr(
        skills,
        "_TOOL_ENV_PROBE",
        "from importlib.metadata import PackageNotFoundError\n"
        "raise PackageNotFoundError('kancil')\n",
    )
    assert (
        skills.installed_kancil_version() is None
    ), "a probe reporting no dist-info reads None (empty stdout)"


def test_s82w2_issue8_repro_renders_the_card(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The issue #8 repro: a 0.0.0-stamped pack now renders the card.

    Rebuilt from issue #8's measured repro (a pack stamped 0.0.0 read
    alignment None with no card while the CLI reported 2.2.5): with the
    route binary reporting 2.2.5, the same pack reads False and the
    NEED HUMAN card names both versions. Red against the pre-fix tree
    (alignment was None off the isolated-install metadata).
    """
    root = _s82w2_campaign(tmp_path)
    pack = _s82w2_pack(root, _s82w2_versioned("0.0.0"))
    _s82w2_patch_route_binary(
        monkeypatch,
        _s82w2_fake_binary(tmp_path, "#!" + sys.executable + "\n"),
    )
    monkeypatch.setattr(skills, "_TOOL_ENV_PROBE", "print('2.2.5')")
    assert skills.version_aligned(pack) is False, (
        "issue #8's 0.0.0 pack must read a known mismatch now (was None)"
    )
    _s82w2_patch_pickup(monkeypatch)
    cards = kanban._skills_cards(root)
    assert len(cards) == 5, f"title plus four sentences expected: {cards!r}"
    assert cards[0] == (
        "- kancil version drift: skills prompt 0.0.0, installed kancil 2.2.5"
        "  [plugins/kancil-base priors frontmatter]"
    ), f"the title must name both versions: {cards[0]!r}"
    assert "0.0.0" in cards[1] and "2.2.5" in cards[1], cards[1]
    rendered = kanban.render(root)
    need_at = rendered.index("NEED HUMAN")
    done_at = rendered.index("\nDONE ")
    card_at = rendered.index("- kancil version drift:")
    assert need_at < card_at < done_at, "the card is not in the NEED HUMAN column"
    monkeypatch.setattr(skills, "_TOOL_ENV_PROBE", "print('junk, not a version')")
    assert (
        skills.version_aligned(pack) is None
    ), "garbage probe keeps the unknown arm (None)"
    assert kanban._skills_cards(root) == [], "an unknown install must not card"


def test_s82w2_alignment_matrix_keeps_three_states(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """equal -> True; either-newer -> False; unknown -> None (binary side)."""
    _s82w2_patch_route_binary(monkeypatch, "/s82w2/never-spawned")

    def make_runner(output: str):
        def _run(_binary: str) -> str:
            return output

        return _run

    equal = _s82w2_pack(_s82w2_campaign(tmp_path), _s82w2_versioned("2.2.5"))
    assert (
        skills.version_aligned(equal, runner=make_runner("2.2.5")) is True
    ), "equal sides must read True"
    prompt_newer = _s82w2_pack(
        _s82w2_campaign(tmp_path, name="s82w2pn"), _s82w2_versioned("2.3.0")
    )
    assert (
        skills.version_aligned(prompt_newer, runner=make_runner("2.2.5")) is False
    ), "prompt-newer must mismatch"
    binary_newer = _s82w2_pack(
        _s82w2_campaign(tmp_path, name="s82w2in"), _s82w2_versioned("2.2.5")
    )
    assert (
        skills.version_aligned(binary_newer, runner=make_runner("2.2.6")) is False
    ), "binary-newer must mismatch"
    unknown = _s82w2_pack(
        _s82w2_campaign(tmp_path, name="s82w2unk"), _s82w2_versioned("2.2.5")
    )
    assert (
        skills.version_aligned(unknown, runner=make_runner("bogus")) is None
    ), "garbage probe is unknown, never a mismatch"
