"""s44 w2 pins — the plugin boundary: pack lint + installer discovery.

Spec-first pins (red against current code) for the s44 contract: the
operator's plugin/hub directive (akar/directives.jsonl seq 2), the
musim/s44.yaml primary_change.expected_band, and DESIGN.md section 16's
proven gates. Spec, interface declarations, and the measured red set:
.rumpun/rimba/s44/w2/notes.md.

Grafting: land this file in tests/ as-is (additions-only; existing suite
files stay untouched). Every helper carries the _s44w2_ prefix, so nothing
collides with existing defs if the file is grafted into test_rumpun.py.

Pinned interface (reconciled to w1's landed module; see notes.md):
- plugin.plugin_lint(pack_dir, manifest) -> list of plugin.PackFinding
  (severity "error"/"warning", message "file:line ..."); the CLI maps
  errors to exit 1.
- plugin.discover_priors(pack_dir) -> sorted full Path list under priors/;
  campaign/ is structurally invisible to it.
- Packs carry manifest.yaml on disk; private_vocabulary is non-empty
  (w1's strict v1 schema); "base" omitted for a base pack.
"""

from __future__ import annotations

from typing import Any

import pytest
import yaml

from rumpun import plugin

# --- shared fixtures ---------------------------------------------------------

# The leak tokens: a source-campaign sid, an absolute path, a private term.
S44W2_SID = "s34"
S44W2_ABS = "/home/operator/datasets/private.csv"
S44W2_TERM = "sampleterm"

S44W2_PRIORS_PATTERN = (
    "Start from a fast, complete baseline before tuning anything.\n"
)

def _s44w2_manifest(**overrides: Any) -> dict[str, Any]:
    """The shared valid manifest; a kwarg set to None removes its field."""
    manifest: dict[str, Any] = {
        "name": "kaggle-base",
        "version": "0.1.0",
        "digest": "a" * 64,
        "private_vocabulary": [S44W2_TERM],
        "source": "seed pack distilled from a prior campaign's proven gates",
    }
    for key, value in overrides.items():
        if value is None:
            manifest.pop(key, None)
        else:
            manifest[key] = value
    return manifest


def _s44w2_pack(tmp_path: Any, files: dict[str, str], manifest: Any = None) -> Any:
    """A fresh pack dir: files at relative paths, manifest.yaml on disk."""
    pack = tmp_path / "pack"
    for rel, text in files.items():
        target = pack / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    if manifest is not None:
        (pack / "manifest.yaml").write_text(
            yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
        )
    return pack


def _s44w2_errors(findings: list[Any]) -> list[str]:
    """Error messages only (house lint.Finding shape: severity/message)."""
    return [
        finding.message
        for finding in findings
        if getattr(finding, "severity", None) == "error"
    ]


def _s44w2_hit(errors: list[str], needle: str) -> bool:
    """True when any error message carries the needle."""
    return any(needle in message for message in errors)


# --- pin 1: a valid minimal pack passes plugin lint --------------------------

def test_s44w2_valid_minimal_pack_passes_plugin_lint(tmp_path: Any) -> None:
    """s44 pin 1 (red: rumpun.plugin does not exist): a valid pack passes.

    priors/ carries clean general knowledge; the manifest carries name,
    version, digest, private_vocabulary, and source. The base lineage field
    is omitted because the seed IS a base pack (base is optional for bases).
    """
    pack = _s44w2_pack(
        tmp_path,
        {"priors/patterns/baseline.md": S44W2_PRIORS_PATTERN},
        manifest=_s44w2_manifest(),
    )
    findings = plugin.plugin_lint(pack, _s44w2_manifest())
    assert _s44w2_errors(findings) == [], _s44w2_errors(findings)

# --- pins 2-4: priors/ leak classes fail naming file and line ----------------

def test_s44w2_sid_in_priors_fails_naming_file_and_line(tmp_path: Any) -> None:
    """s44 pin 2 (red today): a sid token in priors/ fails, file and line named.

    The offense sits on line 7 so the required line marker (7) cannot be
    satisfied spuriously by the token's own digits (s34 carries 3 and 4).
    """
    content = (
        "# a proven gate, distilled\n"
        "\n"
        "Keep the baseline small and complete.\n"
        "\n"
        "Record every verdict, including the negative ones.\n"
        "\n"
        f"Proven in {S44W2_SID} of the source campaign.\n"
    )
    pack = _s44w2_pack(
        tmp_path, {"priors/patterns/leak.md": content}, manifest=_s44w2_manifest()
    )
    findings = plugin.plugin_lint(pack, _s44w2_manifest())
    errors = _s44w2_errors(findings)
    assert _s44w2_hit(errors, "priors/patterns/leak.md"), errors
    assert _s44w2_hit(errors, S44W2_SID), errors
    assert _s44w2_hit(errors, "7"), errors


def test_s44w2_absolute_path_in_priors_fails_naming_file_and_line(
    tmp_path: Any,
) -> None:
    """s44 pin 3 (red today): an absolute path in priors/ fails, file+line named."""
    content = (
        "# path-hygiene pattern\n"
        "\n"
        "Keep every source relative to the pack root.\n"
        "\n"
        "An absolute source cannot survive a pack install.\n"
        "\n"
        f"{S44W2_ABS}\n"
    )
    pack = _s44w2_pack(
        tmp_path, {"priors/patterns/leak.md": content}, manifest=_s44w2_manifest()
    )
    findings = plugin.plugin_lint(pack, _s44w2_manifest())
    errors = _s44w2_errors(list(findings))
    assert _s44w2_hit(errors, "priors/patterns/leak.md"), errors
    assert _s44w2_hit(errors, S44W2_ABS), errors
    assert _s44w2_hit(errors, "7"), errors


def test_s44w2_private_vocabulary_match_fails_naming_file_and_line(
    tmp_path: Any,
) -> None:
    """s44 pin 4 (red today): a declared private term in priors/ fails, file+line named.

    The manifest itself declares the private term; the pack's own published
    surface must not speak it.
    """
    content = (
        "# routing pattern\n"
        "\n"
        "Route names are private vocabulary.\n"
        "\n"
        "The pack speaks public language only.\n"
        "\n"
        f"the {S44W2_TERM} routing applies here\n"
    )
    manifest = _s44w2_manifest(private_vocabulary=[S44W2_TERM])
    pack = _s44w2_pack(
        tmp_path, {"priors/patterns/leak.md": content}, manifest=manifest
    )
    findings = plugin.plugin_lint(pack, manifest)
    errors = _s44w2_errors(list(findings))
    assert _s44w2_hit(errors, "priors/patterns/leak.md"), errors
    assert _s44w2_hit(errors, S44W2_TERM), errors
    assert _s44w2_hit(errors, "7"), errors


# --- pin 5: installer discovery sees priors/ only ----------------------------

def test_s44w2_campaign_dir_invisible_to_installer_discovery(tmp_path: Any) -> None:
    """s44 pin 5 (red today): campaign/ is structurally invisible to discovery.

    A pack carrying a campaign/ dir with sids and secrets installs only its
    priors/ files: discovery returns exactly the priors/ listing, and no
    campaign/ path or secret can appear in it.
    """
    pack = _s44w2_pack(
        tmp_path,
        {
            "priors/patterns/clean.md": S44W2_PRIORS_PATTERN,
            "campaign/results.jsonl": (
                '{"sid": "s41", "secret": "operator-token-hunter2"}\n'
            ),
            "campaign/verdicts.jsonl": '{"sid": "s41", "verdict": "WIN"}\n',
        },
    )
    discovered = plugin.discover_priors(pack)
    rels = sorted(p.relative_to(pack).as_posix() for p in discovered)
    assert rels == ["priors/patterns/clean.md"], rels


# --- pin 6: manifest violations fail -----------------------------------------

@pytest.mark.parametrize("field", ["name", "version", "digest"])
def test_s44w2_manifest_missing_field_fails_naming_field(
    tmp_path: Any, field: str
) -> None:
    """s44 pin 6 (red today): a manifest missing name/version/digest fails.

    Each removal yields at least one error naming the missing field.
    """
    pack = _s44w2_pack(
        tmp_path,
        {"priors/patterns/baseline.md": S44W2_PRIORS_PATTERN},
        manifest=_s44w2_manifest(**{field: None}),
    )
    manifest = _s44w2_manifest(**{field: None})
    errors = _s44w2_errors(list(plugin.plugin_lint(pack, manifest)))
    assert errors, f"no error for missing {field}: {errors}"
    assert _s44w2_hit(errors, field), errors
