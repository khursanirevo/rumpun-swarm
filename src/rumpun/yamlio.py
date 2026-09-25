"""YAML loading with rumpun's ratified trap fixes (DESIGN.md edge cases).

- YAML 1.1 booleans: pyyaml parses the key `on:` as True (the `stop.on` trap).
  We reject any mapping key that is not a string.
- Duplicate keys: pyyaml silently keeps the last. We reject duplicates.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class YamlError(Exception):
    pass


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: yaml.Loader, node: yaml.Node, deep: bool = False) -> dict[Any, Any]:
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            if key in mapping:
                msg = f"duplicate YAML key {key!r}"
                raise YamlError(msg)
        except TypeError as exc:
            msg = f"unhashable mapping key {key!r}"
            raise YamlError(msg) from exc
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def _reject_non_string_keys(node: Any, path: str) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if not isinstance(key, str):
                msg = f"{path}: non-string mapping key {key!r} (YAML 1.1 boolean-key trap)"
                raise YamlError(msg)
            _reject_non_string_keys(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _reject_non_string_keys(item, f"{path}[{index}]")


def load(path: Path) -> Any:
    """Load a YAML file with duplicate-key and non-string-key rejection."""
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        msg = f"{path}: invalid YAML: {exc}"
        raise YamlError(msg) from exc
    if data is None:
        msg = f"{path}: empty YAML document"
        raise YamlError(msg)
    _reject_non_string_keys(data, str(path))
    return data


# s68 w2 (directive seq 6): the campaign reads its own age. Version 1 IS
# today's format; a rumpun.yaml without the key reads as version 1.

SUPPORTED_SCHEMA = (1, 1)


def campaign_schema(root: Path) -> int:
    """The campaign's schema version. A rumpun.yaml without the `schema:`
    key reads as version 1: existing campaigns never refuse."""
    cfg = load(root / "rumpun.yaml")
    raw = cfg.get("schema", 1)
    if isinstance(raw, bool) or not isinstance(raw, int):
        msg = (
            f"{root / 'rumpun.yaml'}: schema must be an int, got {raw!r} "
            f"(supported range: {SUPPORTED_SCHEMA[0]}..{SUPPORTED_SCHEMA[1]})"
        )
        raise YamlError(msg)
    return raw


def require_supported_schema(root: Path) -> int:
    """Mutating verbs refuse campaigns whose schema they cannot read.

    Raises YamlError naming the supported range and pointing at
    .rumpun/CHANGELOG.md; read-only verbs never call this. Returns the
    version when the campaign reads clean.
    """
    version = campaign_schema(root)
    lo, hi = SUPPORTED_SCHEMA
    if not lo <= version <= hi:
        msg = (
            f"rumpun.yaml schema {version} is unsupported (supported range: "
            f"{lo}..{hi}); this reader cannot read that format; see "
            f"{root / 'CHANGELOG.md'} for the schema history"
        )
        raise YamlError(msg)
    return version
