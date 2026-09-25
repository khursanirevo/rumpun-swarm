"""s46 w2 pins — plugin install, list, and use (spec-first, red today).

The s46 band (musim/s46.yaml primary_change.expected_band): WIN when
"plugin install verifies the pack digest and copies priors/ into the
campaign (repro: install then the campaign's plugins dir holds the pack)
AND plugin list shows installed packs (repro) AND init --plugin
kaggle-base scaffolds from the pack's templates and lint profile (repro:
the scaffolded campaign lints clean and its prompts resolve to the pack)
AND the suite is green (188+ tests); LOSS otherwise".

Spec sources: musim/s46.yaml (the band), akar records audit-34 +
s44-harvest (the operator-confirmed plugin/hub arc), and s44's landed
pack format in rumpun/plugin.py. Spec, the pinned interface, and the
measured red set: .rumpun/runs/s46/w2/notes.md.

Grafting: land this file in tests/ as-is (additions-only; existing suite
files stay untouched and the pre-existing suite stays green). Helpers
carry the _s46w2_ prefix so nothing collides with existing defs.

Pinned interface (declared for w1; reconcile at graft, as in s44):
- CLI verbs: `rumpun plugin install <pack-dir>` and `rumpun plugin list`
  run from a campaign root; `rumpun init <target> --plugin <pack-dir>`.
  Install errors exit 1 and name the pack; main() must map PluginError
  to exit 1 (the main() except-tuple does not list it today).
- plugin.resolve_prompt(root, rel) -> Path: the first installed pack
  whose priors tree carries <rel> wins (the pack before the base); the
  fallback is the campaign file root/<rel>. root is the campaign's
  .rumpun dir; installed packs live at root/plugins/<name>/priors/<rel>.
- The digest install verifies: sha256 over the priors/ files sorted by
  pack-relative posix path, updating rel, b"\0", then the file bytes.
  The helper computes it independently; install must match.
- The install record: a file under .rumpun/plugins/<name>/ outside
  priors/ whose text names the pack's name, version, and digest.

cli.main exits: argparse rejects the missing verbs/flags with
SystemExit(2) today; _s46w2_main folds that into rc 2 so every pin
fails on its rc or file assertion, not on an escaping exception.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from rumpun import cli, plugin

S46W2_TERM = "sampleterm"
S46W2_SECRET = "operator-token-s46w2"
S46W2_SID = "s45"

S46W2_EXECUTE_TEMPLATE = (
    "# Execute, pack edition\n"
    "\n"
    "Run the assigned experiments exactly as committed.\n"
)

def _s46w2_priors_digest(pack: Path) -> str:
    """The declared v1 digest: sha256 over sorted priors/ (rel, NUL, bytes)."""
    digest = hashlib.sha256()
    priors = pack / "priors"
    for path in sorted(p for p in priors.rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _s46w2_manifest(digest: str) -> dict[str, Any]:
    """The valid manifest body; digest comes from _s46w2_priors_digest."""
    return {
        "name": "kaggle-base",
        "version": "0.1.0",
        "digest": digest,
        "private_vocabulary": [S46W2_TERM],
        "source": "seed pack distilled from a prior campaign's proven gates",
    }


def _s46w2_pack(tmp_path: Any, *, digest_override: str | None = None) -> Path:
    """A lint-clean pack whose manifest digest matches its priors/ tree.

    priors/ carries a pattern and a prompts/base/execute.md template;
    campaign/ carries a secret that only pin 6 should ever look for.
    """
    pack = tmp_path / "kaggle-base-pack"
    (pack / "priors" / "patterns").mkdir(parents=True)
    (pack / "priors" / "patterns" / "baseline.md").write_text(
        "Start from a fast, complete baseline before tuning anything.\n",
        encoding="utf-8",
    )
    (pack / "priors" / "prompts" / "base").mkdir(parents=True)
    (pack / "priors" / "prompts" / "base" / "execute.md").write_text(
        S46W2_EXECUTE_TEMPLATE, encoding="utf-8"
    )
    (pack / "campaign").mkdir()
    (pack / "campaign" / "verdicts.jsonl").write_text(
        f'{{"sid": "{S46W2_SID}", "secret": "{S46W2_SECRET}"}}\n',
        encoding="utf-8",
    )
    digest = digest_override or _s46w2_priors_digest(pack)
    (pack / "manifest.yaml").write_text(
        yaml.safe_dump(_s46w2_manifest(digest), sort_keys=False),
        encoding="utf-8",
    )
    return pack


def _s46w2_campaign(tmp_path: Any) -> Path:
    """A scaffolded campaign root; the cwd that resolves _project_root."""
    root = tmp_path / "campaign"
    assert cli.main(["init", str(root)]) == 0
    return root


def _s46w2_main(argv: list[str]) -> int:
    """cli.main with argparse's SystemExit folded into rc 2."""
    try:
        return cli.main(argv)
    except SystemExit as exc:
        return int(exc.code or 0)


def _s46w2_output(capsys: Any) -> str:
    """Combined stdout+stderr since house verbs split print and logger."""
    cap = capsys.readouterr()
    return cap.out + cap.err


def _s46w2_record_text(installed: Path) -> str:
    """Concatenated text of every non-priors file under the install dir."""
    chunks: list[str] = []
    for path in sorted(installed.rglob("*")):
        if path.is_file() and "priors" not in path.relative_to(installed).parts:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


# --- pin 1: a valid pack installs with priors/ and the record ----------------

def test_s46w2_install_copies_priors_and_writes_record(
    tmp_path: Any, monkeypatch: Any, capsys: Any
) -> None:
    """s46 pin 1 (red today: the plugin verbs do not exist)."""
    pack = _s46w2_pack(tmp_path)
    root = _s46w2_campaign(tmp_path)
    monkeypatch.chdir(root)
    rc = _s46w2_main(["plugin", "install", str(pack)])
    out = _s46w2_output(capsys)
    assert rc == 0, out
    installed = root / ".rumpun" / "plugins" / "kaggle-base"
    assert (installed / "priors" / "patterns" / "baseline.md").is_file()
    template = installed / "priors" / "prompts" / "base" / "execute.md"
    assert template.read_text(encoding="utf-8") == S46W2_EXECUTE_TEMPLATE
    record = _s46w2_record_text(installed)
    assert "kaggle-base" in record, record
    assert "0.1.0" in record, record
    assert _s46w2_priors_digest(pack) in record, record


# --- pin 2: a tampered pack is refused, naming the pack -----------------------

def test_s46w2_install_refuses_tampered_pack_naming_it(
    tmp_path: Any, monkeypatch: Any, capsys: Any
) -> None:
    """s46 pin 2 (red today: the plugin verbs do not exist).

    The manifest digest is 64-hex but wrong for the priors/ tree, so the
    refusal must be the content check, not the format check.
    """
    pack = _s46w2_pack(tmp_path, digest_override="b" * 64)
    root = _s46w2_campaign(tmp_path)
    monkeypatch.chdir(root)
    rc = _s46w2_main(["plugin", "install", str(pack)])
    out = _s46w2_output(capsys)
    assert rc == 1, out
    assert "kaggle-base" in out, out
    installed = root / ".rumpun" / "plugins" / "kaggle-base"

    assert not installed.exists(), out


# --- pin 3: plugin list shows name, version, digest ---------------------------

def test_s46w2_list_shows_name_version_digest(
    tmp_path: Any, monkeypatch: Any, capsys: Any
) -> None:
    """s46 pin 3 (red today: the plugin verbs do not exist)."""
    pack = _s46w2_pack(tmp_path)
    root = _s46w2_campaign(tmp_path)
    monkeypatch.chdir(root)
    assert _s46w2_main(["plugin", "install", str(pack)]) == 0
    _s46w2_output(capsys)  # drain the install capture
    rc = _s46w2_main(["plugin", "list"])
    out = _s46w2_output(capsys)
    assert rc == 0, out
    assert "kaggle-base" in out, out
    assert "0.1.0" in out, out
    assert _s46w2_priors_digest(pack) in out, out


# --- pin 4: init --plugin scaffolds; the campaign lints clean -----------------

def test_s46w2_init_plugin_scaffolds_and_lints_clean(
    tmp_path: Any, monkeypatch: Any, capsys: Any
) -> None:
    """s46 pin 4 (red today: init has no --plugin flag).

    The band's repro is "the scaffolded campaign lints clean"; a plain
    scaffold lints dirty today (empty goal/metric), so --plugin mode must
    seed the campaign from the pack's manifest. Probe evidence:
    scratch/probe_scaffold_lint.out.
    """
    pack = _s46w2_pack(tmp_path)
    target = tmp_path / "fresh"
    monkeypatch.chdir(tmp_path)
    rc = _s46w2_main(["init", str(target), "--plugin", str(pack)])
    out = _s46w2_output(capsys)
    assert rc == 0, out
    installed = target / ".rumpun" / "plugins" / "kaggle-base" / "priors"
    assert (installed / "patterns" / "baseline.md").is_file()
    s1 = target / ".rumpun" / "seasons" / "s1.yaml"
    lint_rc = _s46w2_main(["lint", str(s1)])
    out2 = _s46w2_output(capsys)
    assert lint_rc == 0, out2


# --- pin 5: prompts resolve to the pack before the base -----------------------

def test_s46w2_prompts_resolve_pack_before_base(tmp_path: Any, monkeypatch: Any) -> None:
    """s46 pin 5 (red today: plugin.resolve_prompt does not exist).

    Fixture arranges the installed tree directly (the layout pin 1 holds
    install to), so this pin red-isolates the resolution capability.
    """
    pack = _s46w2_pack(tmp_path)
    root = _s46w2_campaign(tmp_path)
    monkeypatch.chdir(root)
    dot = root / ".rumpun"
    src = pack / "priors" / "prompts" / "base" / "execute.md"
    dst = dot / "plugins" / "kaggle-base" / "priors" / "prompts" / "base"
    dst.mkdir(parents=True)
    (dst / "execute.md").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    resolved = plugin.resolve_prompt(dot, "prompts/base/execute.md")
    assert resolved.read_text(encoding="utf-8") == S46W2_EXECUTE_TEMPLATE


def test_s46w2_prompts_fall_back_to_base(tmp_path: Any, monkeypatch: Any) -> None:
    """s46 pin 5b (red today: plugin.resolve_prompt does not exist)."""
    root = _s46w2_campaign(tmp_path)
    monkeypatch.chdir(root)
    resolved = plugin.resolve_prompt(
        root / ".rumpun", "prompts/base/analyze.md"
    )
    assert resolved == root / ".rumpun" / "prompts" / "base" / "analyze.md"
    assert resolved.is_file()


# --- pin 6: campaign/ content never lands in the campaign ---------------------

def test_s46w2_campaign_content_never_installs(
    tmp_path: Any, monkeypatch: Any, capsys: Any
) -> None:
    """s46 pin 6 (red today: init has no --plugin flag).

    The pack carries campaign/verdicts.jsonl with a secret and a sid; the
    scaffolded campaign must carry neither anywhere under its .rumpun.
    """
    pack = _s46w2_pack(tmp_path)
    target = tmp_path / "fresh"
    monkeypatch.chdir(tmp_path)
    rc = _s46w2_main(["init", str(target), "--plugin", str(pack)])
    assert rc == 0, _s46w2_output(capsys)
    dot = target / ".rumpun"
    for path in dot.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            assert S46W2_SECRET not in text, path
            assert S46W2_SID not in text, path
    assert not (dot / "plugins" / "kaggle-base" / "campaign").exists()

