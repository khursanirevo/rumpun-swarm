"""s83 w2 pins — the distill-lint contract, pinned from the other side.

Spec source: .rumpun/runs/s83/w2/prompt.md and the s83 season yaml
(code-span tokens, absolute paths, parent escapes cannot seal silently;
distill and install cannot disagree). Ground truth is issue #10: the
hand-distilled kancil-base draft sealed with zero findings while
carrying `/error-exp` in a code span; the s81 install gate was the
first lint pass that ever saw it. All pins are offline and in-process:
adversarial content enters through a monkeypatched DISTILLED_SECTIONS
(the only injection point — plugin_distill emits fixed bodies), every
pack is a fixture under tmp_path, the real kancil-base draft is never
touched, no route call, no network.

Contract these pins hold -- src/rumpun/plugin.py:

1. The adversarial seal shapes (issue #10's `/error-exp` backtick span,
   an absolute path in plain text, a parent-relative `../` escape)
   never seal silently: the distill either refuses (PluginError, no
   draft left behind) or seals with the finding recorded in the
   manifest. A silent seal with no recorded finding fails the pin.
2. The digest invariant: the sealed manifest's digest equals a fresh
   INDEPENDENT recompute over the sealed priors (the s46w2/s81 three-way
   convention: declared == source == installed copy), before and after
   a refused-then-fixed re-seal.
3. Gate agreement: for the same content, distill's decision and
   install's decision agree — both flag the adversarial shape, both
   accept the clean shape (install promotes the sealed draft).
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

import pytest
import yaml

from rumpun import plugin as plugin_mod

logger = logging.getLogger(__name__)

S83W2_PACK = "lint-pin"

_S83W2_CODE_SPAN_BODY = (
    "# The lint-pin prior\n"
    "\n"
    "Pointer labels stay relative: `/error-exp` names the error route.\n"
)
_S83W2_PLAIN_ABS_BODY = (
    "# The lint-pin prior\n"
    "\n"
    "The shared probe lives at /usr/local/bin/lintpin and stays a fixture.\n"
)
_S83W2_PARENT_ESCAPE_BODY = (
    "# The lint-pin prior\n"
    "\n"
    "Merge context from ../lintpin/priors.md before summarizing.\n"
)
_S83W2_CLEAN_BODY = (
    "# The lint-pin prior\n"
    "\n"
    "Pointer labels stay relative; the pack names no campaign root.\n"
)


# --- helpers (all carry the _s83w2_ prefix) ----------------------------------


def _s83w2_independent_digest(pack: Path) -> str:
    """The declared v1 digest: sha256 over sorted priors/ (rel, NUL, bytes).

    Deliberately not plugin_mod.priors_digest: the pin recomputes the
    hash independently (the s46w2 convention), so a broken priors_digest
    cannot satisfy both sides of the comparison.
    """
    digest = hashlib.sha256()
    priors = pack / "priors"
    for path in sorted(p for p in priors.rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _s83w2_campaign(tmp_path: Path, tag: str) -> Path:
    """One throwaway campaign whose ratified corpus evidences the pin prior.

    The corpus overlay is the _distill_corpus surface (DESIGN.md plus
    .rumpun/ledger/*.md); "lintpin" is the evidence word the injected
    prior matches. Nothing outside tmp_path is written.
    """
    root = tmp_path / tag / "proj"
    (root / ".rumpun" / "ledger").mkdir(parents=True)
    (root / "DESIGN.md").write_text(
        "lintpin evidence: the fixture campaign ratified the lint-pin "
        "prior class for the s83 pins.\n",
        encoding="utf-8",
    )
    (root / ".rumpun" / "ledger" / "2026-01-01_lintpin.md").write_text(
        "lintpin evidence in a fixture ledger record.\n", encoding="utf-8"
    )
    return root


def _s83w2_distill(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    root: Path,
    body: str,
) -> tuple[bool, Path, str]:
    """Run the real plugin_distill with one injected prior body.

    Returns (sealed, draft dir, decision text). sealed=True iff the
    draft landed; PluginError folds into the decision text together
    with the captured logs, so the caller can demand the finding named
    on the sealed path.
    """
    prior = plugin_mod.DistilledPrior(
        key=S83W2_PACK,
        title="The lint-pin prior",
        evidence=(re.compile("lintpin", re.IGNORECASE),),
        body=body,
    )
    monkeypatch.setattr(
        plugin_mod, "DISTILLED_SECTIONS", (("", (prior,)),), raising=True
    )
    caplog.set_level(logging.DEBUG)
    dest = plugin_mod.plugins_dir(root) / f"{S83W2_PACK}-draft"
    try:
        plugin_mod.plugin_distill(root, S83W2_PACK, "the s83 lint pins fixture")
    except plugin_mod.PluginError as exc:
        return False, dest, caplog.text + "\n" + str(exc)
    manifest_text = ""
    manifest_path = dest / plugin_mod.MANIFEST_NAME
    if manifest_path.is_file():
        manifest_text = manifest_path.read_text(encoding="utf-8")
    return True, dest, caplog.text + "\n" + manifest_text


def _s83w2_assert_never_silent(sealed: bool, text: str, token: str, dest: Path) -> None:
    """The contract: refuse, or record the finding — never seal silently.

    A refusal must not leave a draft behind; a seal must name the
    offending token in the decision surfaces (manifest findings under
    w1's record shape, the logged findings under the refusal shape).
    """
    if not sealed:
        assert not dest.exists(), "a refused distill must not leave a draft behind"
        return
    assert token in text, (
        f"silent seal: the draft landed with no recorded finding naming {token!r}"
    )


def _s83w2_hand_pack(tmp_path: Path, tag: str, skills_text: str) -> Path:
    """A hand-built kancil-base draft mirror with the digest sealed over
    its adversarial priors (the s67-era shape the s81 gate refused)."""
    pack = tmp_path / "packs" / tag
    skills_dir = pack / "priors" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "kancil-2.2-skills.md").write_text(skills_text, encoding="utf-8")
    manifest = {
        "name": "kancil-base",
        "version": "0.1.0",
        "digest": _s83w2_independent_digest(pack),
        "private_vocabulary": ["sid"],
        "source": "the campaign's proven gates and patterns",
    }
    (pack / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return pack


def _s83w2_reseal(pack: Path) -> str:
    """Recompute the digest over priors/ and rewrite the manifest line
    (the authorized s82 re-seal shape)."""
    manifest_path = pack / plugin_mod.MANIFEST_NAME
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["digest"] = _s83w2_independent_digest(pack)
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return manifest["digest"]


# --- contract 1: the adversarial seal shapes ---------------------------------


def test_s83w2_code_span_token_never_seals_silently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """`/error-exp` in a backtick span: issue #10's exact shape."""
    root = _s83w2_campaign(tmp_path, "s83w2-span")
    sealed, dest, text = _s83w2_distill(
        monkeypatch, caplog, root, _S83W2_CODE_SPAN_BODY
    )
    _s83w2_assert_never_silent(sealed, text, "/error-exp", dest)


def test_s83w2_plain_text_absolute_path_never_seals_silently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """An absolute path in plain text trips ABS_PATH_RE without a span."""
    root = _s83w2_campaign(tmp_path, "s83w2-abs")
    sealed, dest, text = _s83w2_distill(
        monkeypatch, caplog, root, _S83W2_PLAIN_ABS_BODY
    )
    _s83w2_assert_never_silent(sealed, text, "/usr/local/bin/lintpin", dest)


def test_s83w2_parent_escape_never_seals_silently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A `../` escape stays inside the never-silent contract.

    Spec-first red on main: no lint pattern matches a parent-relative
    escape today, so the distill seals it with no finding anywhere.
    The season band names this shape; the gate must refuse it or
    record it.
    """
    root = _s83w2_campaign(tmp_path, "s83w2-escape")
    sealed, dest, text = _s83w2_distill(
        monkeypatch, caplog, root, _S83W2_PARENT_ESCAPE_BODY
    )
    _s83w2_assert_never_silent(sealed, text, "../lintpin/priors.md", dest)


# --- contract 2: the digest invariant ----------------------------------------


def test_s83w2_seal_digest_matches_fresh_recompute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The sealed manifest digest equals the independent recompute."""
    root = _s83w2_campaign(tmp_path, "s83w2-digest")
    sealed, dest, text = _s83w2_distill(monkeypatch, caplog, root, _S83W2_CLEAN_BODY)
    assert sealed, f"the clean control must seal; decision text:\n{text}"
    manifest = yaml.safe_load((dest / plugin_mod.MANIFEST_NAME).read_text())
    assert manifest["digest"] == _s83w2_independent_digest(dest)
    assert manifest["name"] == S83W2_PACK


def test_s83w2_digest_holds_after_refused_then_fixed_reseal(tmp_path: Path) -> None:
    """The s82 story end to end: adversarial pack seals a valid digest,
    install refuses the content, the one-token fix re-seals, the gate
    passes, and the three-way digest convention holds on the install."""
    root = _s83w2_campaign(tmp_path, "s83w2-reseal")
    pack = _s83w2_hand_pack(tmp_path, "s83w2-reseal-pack", _S83W2_CODE_SPAN_BODY)
    sealed_manifest = yaml.safe_load((pack / plugin_mod.MANIFEST_NAME).read_text())
    assert sealed_manifest["digest"] == _s83w2_independent_digest(pack)
    with pytest.raises(plugin_mod.PluginError) as excinfo:
        plugin_mod.plugin_install(root, pack)
    assert "refused" in str(excinfo.value)
    assert not (plugin_mod.plugins_dir(root) / "kancil-base").exists()
    skills = pack / "priors" / "skills" / "kancil-2.2-skills.md"
    skills.write_text(
        skills.read_text(encoding="utf-8").replace("/error-exp", "error-exp"),
        encoding="utf-8",
    )
    resealed_digest = _s83w2_reseal(pack)
    plugin_mod.plugin_install(root, pack)
    installed = plugin_mod.plugins_dir(root) / "kancil-base"
    installed_manifest = yaml.safe_load((installed / plugin_mod.MANIFEST_NAME).read_text())
    assert installed_manifest["digest"] == _s83w2_independent_digest(installed)
    assert installed_manifest["digest"] == resealed_digest
    assert [row["name"] for row in plugin_mod.plugin_list(root)] == ["kancil-base"]


# --- contract 3: the gates cannot disagree -----------------------------------


def test_s83w2_gates_agree_on_the_adversarial_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Same content, two gates: the distill never passes it clean and
    install refuses it. Holds under the refusal shape and the
    recorded-findings shape alike."""
    root = _s83w2_campaign(tmp_path, "s83w2-agree-bad")
    sealed, _dest, text = _s83w2_distill(
        monkeypatch, caplog, root, _S83W2_CODE_SPAN_BODY
    )
    distill_rejects = (not sealed) or ("/error-exp" in text)
    assert distill_rejects, "the distill accepted the adversarial shape silently"
    pack = _s83w2_hand_pack(tmp_path, "s83w2-agree-bad-pack", _S83W2_CODE_SPAN_BODY)
    with pytest.raises(plugin_mod.PluginError):
        plugin_mod.plugin_install(root, pack)


def test_s83w2_gates_agree_on_clean_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Clean content: the distill seals and install promotes the sealed
    draft; the registry lists it."""
    root = _s83w2_campaign(tmp_path, "s83w2-agree-clean")
    sealed, dest, text = _s83w2_distill(monkeypatch, caplog, root, _S83W2_CLEAN_BODY)
    assert sealed, f"the clean control must seal; decision text:\n{text}"
    plugin_mod.plugin_install(root, dest)
    installed = plugin_mod.plugins_dir(root) / S83W2_PACK
    assert (installed / plugin_mod.MANIFEST_NAME).is_file()
    assert [row["name"] for row in plugin_mod.plugin_list(root)] == [S83W2_PACK]
