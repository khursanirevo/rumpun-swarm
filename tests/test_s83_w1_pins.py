"""s83 w1 pins — the distill seal runs the content lint install runs (issue #10).

Spec sources: .rumpun/prompts/dev/w1-distill-lint.md (the lane brief),
issue #10 (khursanirevo/rumpun), DESIGN.md s81 (the defect record), and
the landed s50/s51 distill shape in rumpun/plugin.py.

The landed shape (this season): a re-distill carries the existing draft's
priors/ content forward -- the hand-maintained files a wholesale replace
would silently drop (the kancil skills prompt, the late repro-backed-
closure template) -- so the SAME content lint plugin install applies
gates the full staged tree at seal time. A violating carried file refuses
the seal (rc 1, findings logged) with the previous draft left untouched;
after the fix, the re-distill seals with the digest over the merged tree
and the install gate passes on the sealed draft.

Red today (main): plugin_distill replaces an existing draft wholesale, so
a hand-sealed violating draft silently vanishes and the re-distill exits
0 -- pin 1 fails on the rc assertion, the spec reason.

Grafting: land this file in tests/ as-is (additions-only; no existing
suite file touched). Helpers carry the _s83w1_ prefix. Offline: all
writes stay in the fixture's tmp tree; the only subprocess calls are
`python -m rumpun init/plugin ...` against the fixture campaign; no
network, no live route call, no .rumpun state edits in the source repo.

The fixture (module-scoped) replays the issue end to end in one tmp
campaign, one subprocess per stage:
  stage A  distill #1 -- the clean first seal
  stage B  the s80 replay: a violating token (the issue's own
           ``/error-exp`` in a code span) lands in a carried skills file
           and the manifest digest is re-sealed BY HAND over it -- an
           internally consistent, uninstallable draft
  stage C  distill #2 -- the seal must refuse; the draft stays untouched
  stage D  the s82 replay: the one-token reword
  stage E  distill #3 -- the clean re-seal over the merged tree
  stage F  plugin install -- the gate passes on the sealed draft
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

from rumpun import plugin

S83W1_PACK_NAME = "kancil-base"
S83W1_SOURCE_NOTE = "the campaign's proven gates and patterns"
S83W1_CARRIED_REL = "priors/skills/kancil-2.2-skills.md"
S83W1_VIOLATION = "an empty eval exits 1 with an `/error-exp` pointer"
S83W1_REWORD = "an empty eval exits 1 with an `error-exp` pointer"
S83W1_TIMEOUT = 120


def _s83w1_repo() -> Path:
    """The repo root: the first pyproject.toml walking up from this file."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s83w1_env() -> dict[str, str]:
    """The subprocess env with the repo's src/ prepended to PYTHONPATH."""
    env = dict(os.environ)
    src = str(_s83w1_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s83w1_run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """One `python -m rumpun <argv>` subprocess from cwd, 120s bounded."""
    try:
        return subprocess.run(
            [sys.executable, "-m", "rumpun", *argv],
            cwd=str(cwd),
            env=_s83w1_env(),
            capture_output=True,
            text=True,
            timeout=S83W1_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(f"rumpun {' '.join(argv)} exceeded {S83W1_TIMEOUT}s") from exc


def _s83w1_priors_digest(pack: Path) -> str:
    """The declared v1 digest: sha256 over sorted priors/ (rel, NUL, bytes)."""
    digest = hashlib.sha256()
    priors = pack / "priors"
    for path in sorted(p for p in priors.rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _s83w1_priors_texts(pack: Path) -> list[tuple[str, str]]:
    """(rel posix path, text) for every file under pack/priors/, sorted."""
    priors = pack / "priors"
    out: list[tuple[str, str]] = []
    for path in sorted(priors.rglob("*")):
        if path.is_file():
            rel = path.relative_to(pack).as_posix()
            out.append((rel, path.read_text(encoding="utf-8", errors="replace")))
    return out


def _s83w1_manifest(draft: Path) -> dict[str, Any]:
    """The draft's manifest, strictly loaded; a legible red when unloadable."""
    try:
        return plugin.load_manifest(draft)
    except plugin.PluginError as exc:
        pytest.fail(f"{draft}: manifest does not load: {exc}")


def _s83w1_gate_campaign(tmp: Path) -> Path:
    """A scaffolded campaign overlaid with this campaign's scan surface.

    The s50/s51 pin shape: `rumpun init`, then the real rumpun.yaml, season
    yamls, ledger records, DESIGN.md, and GLOSSARY.md -- the material the
    distill's scan reads -- overlaid without mutating the source campaign.
    """
    repo = _s83w1_repo()
    campaign = tmp / "campaign"
    proc = _s83w1_run(tmp, ["init", str(campaign)])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    dot = campaign / ".rumpun"
    shutil.copytree(repo / ".rumpun" / "seasons", dot / "seasons", dirs_exist_ok=True)
    shutil.copytree(repo / ".rumpun" / "ledger", dot / "ledger", dirs_exist_ok=True)
    for name in ("DESIGN.md", "GLOSSARY.md"):
        shutil.copy2(repo / name, campaign / name)
    shutil.copy2(repo / ".rumpun" / "rumpun.yaml", dot / "rumpun.yaml")
    return campaign


@pytest.fixture(scope="module")
def s83w1_reseal(tmp_path_factory: pytest.TempPathFactory) -> SimpleNamespace:
    """The issue #10 replay: seal, violate, refuse, reword, re-seal, install."""
    tmp = tmp_path_factory.mktemp("s83w1")
    campaign = _s83w1_gate_campaign(tmp)
    draft = campaign / ".rumpun" / "plugins" / f"{S83W1_PACK_NAME}-draft"

    # stage A: the clean first seal (no pre-existing draft: fresh emission)
    proc_a = _s83w1_run(
        campaign,
        ["plugin", "distill", S83W1_PACK_NAME, "--source", S83W1_SOURCE_NOTE],
    )
    assert proc_a.returncode == 0, proc_a.stdout + proc_a.stderr
    assert draft.is_dir(), str(draft)

    # stage B: the s80 replay -- a carried violating token, re-sealed by hand
    skills = draft / S83W1_CARRIED_REL
    skills.parent.mkdir(parents=True, exist_ok=True)
    skills.write_text(S83W1_VIOLATION + "\n", encoding="utf-8")
    manifest = plugin.load_manifest(draft)
    manifest["digest"] = plugin.priors_digest(draft)
    (draft / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    sealed_digest = manifest["digest"]
    assert sealed_digest == _s83w1_priors_digest(draft)

    # stage C: the re-distill must refuse; a refusal changes nothing
    proc_c = _s83w1_run(
        campaign,
        ["plugin", "distill", S83W1_PACK_NAME, "--source", S83W1_SOURCE_NOTE],
    )
    out_c = proc_c.stdout + proc_c.stderr
    # the refusal leaves the previous draft exactly as stage B sealed it
    refused_digest = plugin.load_manifest(draft)["digest"]
    refused_text = (draft / S83W1_CARRIED_REL).read_text(encoding="utf-8")

    # stage D: the s82 replay -- the one-token reword
    skills.write_text(S83W1_REWORD + "\n", encoding="utf-8")

    # stage E: the clean re-seal over the merged tree
    proc_e = _s83w1_run(
        campaign,
        ["plugin", "distill", S83W1_PACK_NAME, "--source", S83W1_SOURCE_NOTE],
    )
    out_e = proc_e.stdout + proc_e.stderr

    # stage F: the install gate on the sealed draft
    proc_f = _s83w1_run(campaign, ["plugin", "install", str(draft)])
    out_f = proc_f.stdout + proc_f.stderr

    return SimpleNamespace(
        campaign=campaign,
        draft=draft,
        sealed_digest=sealed_digest,
        proc_c=proc_c,
        out_c=out_c,
        refused_digest=refused_digest,
        refused_text=refused_text,
        proc_e=proc_e,
        out_e=out_e,
        proc_f=proc_f,
        out_f=out_f,
        texts=lambda: _s83w1_priors_texts(draft),
        manifest=lambda: _s83w1_manifest(draft),
        computed_digest=lambda: _s83w1_priors_digest(draft),
    )


# --- pin 1: a violating carried draft refuses to seal, unchanged --------------

def test_s83w1_violating_draft_refuses_to_seal(s83w1_reseal: SimpleNamespace) -> None:
    """s83 w1 pin 1: the uninstallable draft cannot re-seal silently.

    Stage C: the re-distill over a hand-sealed draft carrying ``/error-exp``
    in a code span exits nonzero, the refusal names the finding, and the
    previous draft is left exactly as it stood (the manifest digest still
    the hand-sealed value; the violating file still carrying the token).
    """
    ns = s83w1_reseal
    assert ns.proc_c.returncode != 0, ns.out_c
    assert "refused" in ns.out_c, ns.out_c
    assert "/error-exp" in ns.out_c, ns.out_c
    assert ns.refused_digest == ns.sealed_digest, ns.out_c
    assert "/error-exp" in ns.refused_text, ns.refused_text


def test_s83w1_clean_reseal_carries_merged_tree(s83w1_reseal: SimpleNamespace) -> None:
    """s83 w1 pin 2: the reworded draft re-seals over the merged tree.

    Stage E: the re-distill exits 0; the carried skills file survives into
    the sealed draft (now carrying the reworded token); the emitted classes
    stay; the manifest digest verifies three ways (manifest == independent
    recompute == plugin.priors_digest over the sealed priors/ tree).
    """
    ns = s83w1_reseal
    assert ns.proc_e.returncode == 0, ns.out_e
    texts = dict(ns.texts())
    assert S83W1_CARRIED_REL in texts, sorted(texts)
    assert "/error-exp" not in texts[S83W1_CARRIED_REL], texts[S83W1_CARRIED_REL]
    assert "error-exp" in texts[S83W1_CARRIED_REL], texts[S83W1_CARRIED_REL]
    assert "priors/falsify-enforcement.md" in texts, sorted(texts)
    digest = ns.manifest()["digest"]
    assert digest == ns.computed_digest(), (digest, ns.computed_digest())
    assert digest == plugin.priors_digest(ns.draft), digest


def test_s83w1_install_gate_passes_on_sealed_draft(s83w1_reseal: SimpleNamespace) -> None:
    """s83 w1 pin 3: the install gate passes on the sealed draft.

    Stage F: `plugin install` on the re-sealed draft exits 0; the installed
    pack carries the draft's exact priors/ rel set; the registry row and
    the installed manifest both carry the draft's digest.
    """
    ns = s83w1_reseal
    assert ns.proc_f.returncode == 0, ns.out_f
    installed = ns.campaign / ".rumpun" / "plugins" / S83W1_PACK_NAME
    assert (installed / "manifest.yaml").is_file(), str(installed)
    draft_rels = {rel for rel, _ in ns.texts()}
    installed_rels = {rel for rel, _ in _s83w1_priors_texts(installed)}
    assert installed_rels == draft_rels, (sorted(draft_rels), sorted(installed_rels))
    digest = ns.manifest()["digest"]
    records = {record["name"]: record for record in plugin.plugin_list(ns.campaign)}
    assert S83W1_PACK_NAME in records, sorted(records)
    assert records[S83W1_PACK_NAME]["digest"] == digest
    assert plugin.load_manifest(installed)["digest"] == digest
