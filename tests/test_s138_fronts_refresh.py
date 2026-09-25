"""s138 w1 pins: the fronts file reflects the standing truth.

Spec source: the s138 w1 brief. .rumpun/operator-fronts.yaml is the
report index's Standing decisions card (s131 w1); the truth it must
reflect lives in .rumpun/RESUME.md's open items, refreshed this lane.
The pin's subject is the file's FORMAT: the file parses as a non-empty
list of non-empty strings, and every entry names its owner (the
operator). The malformed shapes are the brief's red: each synthesized
fixture below must be rejected by the format rules. Fixture
discipline: the real file is read read-only; every malformed shape is
a tmp_path synthesis, no writes to the repo. The render itself is
pinned by the s131 file; this file pins format only, so a future
content refresh needs no pin edit.
"""

from __future__ import annotations

from pathlib import Path

import yaml

FRONTS = Path(__file__).resolve().parents[1] / ".rumpun" / "operator-fronts.yaml"


def _load(path: Path) -> object:
    """Parse fronts yaml; unparsable text reads back as None (rejected)."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None


def _fronts_ok(data: object) -> bool:
    """Non-empty list of non-empty strings, every entry naming its owner."""
    if not isinstance(data, list) or not data:
        return False
    return all(
        isinstance(entry, str) and entry.strip() and "operator" in entry.lower()
        for entry in data
    )


def test_s138fr_real_file_is_format_valid() -> None:
    """The standing file: parses, non-empty, owner named on every entry."""
    data = _load(FRONTS)
    assert _fronts_ok(data), f"invalid fronts: {data!r}"


def test_s138fr_unparsable_yaml_rejected(tmp_path: Path) -> None:
    path = tmp_path / "fronts.yaml"
    path.write_text("::: not yaml [\n", encoding="utf-8")
    assert not _fronts_ok(_load(path))


def test_s138fr_non_list_body_rejected(tmp_path: Path) -> None:
    path = tmp_path / "fronts.yaml"
    path.write_text("fronts: not a list\n", encoding="utf-8")
    assert not _fronts_ok(_load(path))


def test_s138fr_non_string_entry_rejected(tmp_path: Path) -> None:
    path = tmp_path / "fronts.yaml"
    path.write_text('- "named (operator)"\n- 42\n', encoding="utf-8")
    assert not _fronts_ok(_load(path))


def test_s138fr_empty_body_or_entry_rejected(tmp_path: Path) -> None:
    path = tmp_path / "fronts.yaml"
    path.write_text("", encoding="utf-8")
    assert not _fronts_ok(_load(path))
    path.write_text("[]\n", encoding="utf-8")
    assert not _fronts_ok(_load(path))
    path.write_text('- ""\n', encoding="utf-8")
    assert not _fronts_ok(_load(path))
    path.write_text('- "   "\n', encoding="utf-8")
    assert not _fronts_ok(_load(path))


def test_s138fr_ownerless_entry_rejected(tmp_path: Path) -> None:
    path = tmp_path / "fronts.yaml"
    path.write_text('- "the forge merge decision table"\n', encoding="utf-8")
    assert not _fronts_ok(_load(path))
