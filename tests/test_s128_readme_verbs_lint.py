"""s128 w1: the README verbs table stays parseable against the CLI parser.

The guide's shell-fenced commands carry the s121 parser lint; the README's
verbs table can drift silently. Every `## Verbs` table row's command cell
must name a verb (and subverbs for the season/evolve/plugin/ledger
families) the parser accepts, and every --flag the cell names must be a
known option of that leaf. The reverse direction holds too: every parser
verb and every family subverb needs a table row, so a new verb cannot
ship undocumented. Prose cells stay out of scope, as in the s121 pin.
"""

from __future__ import annotations

import re
from pathlib import Path

from rumpun import cli

REPO = Path(__file__).resolve().parents[1]
README = REPO / "README.md"
FAMILIES = {"season", "evolve", "plugin", "ledger"}
VERBS_SECTION = re.compile(r"^## Verbs\n(.*?)(?=^## )", re.DOTALL | re.MULTILINE)


def _table_rows() -> list[str]:
    text = README.read_text()
    block = VERBS_SECTION.search(text)
    assert block, "README.md carries no '## Verbs' section"
    rows = [line for line in block.group(1).splitlines() if line.startswith("| `")]
    assert rows, "the README verbs table carries no command rows"
    return rows


def _row_command(row: str) -> tuple[str, list[str], list[str], str]:
    """Split a row's command cell into verb, subverbs, flags, and the cell."""
    cell = row.split("|")[1].strip()
    bare = cell.strip("`")
    tokens = [t.strip(",") for t in bare.replace("[", " ").replace("]", " ").split()]
    verb = tokens[0]
    flags = [t for t in tokens[1:] if t.startswith("--")]
    subverbs = [t for t in tokens[1:] if not t.startswith("--") and not t.isupper()]
    return verb, subverbs, flags, cell


def test_every_table_row_lints_against_the_parser() -> None:
    """Each row's command cell parses against its parser leaf."""
    choices = cli.build_parser()._subparsers._group_actions[0].choices
    for row in _table_rows():
        verb, subverbs, flags, cell = _row_command(row)
        assert verb in choices, f"{cell!r}: unknown verb {verb!r}"
        leaf = choices[verb]
        if verb in FAMILIES:
            sub_choices = leaf._subparsers._group_actions[0].choices
            assert subverbs, f"{cell!r}: family {verb!r} names no subverbs"
            unknown = [s for s in subverbs if s not in sub_choices]
            assert not unknown, f"{cell!r}: unknown {verb} subverbs {unknown}"
            leaves = [sub_choices[s] for s in subverbs]
        else:
            leaves = [leaf]
        known = {
            opt
            for lf in leaves
            for action in lf._actions
            for opt in action.option_strings
        }
        unnamed = [f for f in flags if f not in known]
        assert not unnamed, f"{cell!r}: unknown flags {unnamed}"


def test_every_parser_verb_has_a_table_row() -> None:
    """The parser cannot grow a verb without a README table row."""
    choices = cli.build_parser()._subparsers._group_actions[0].choices
    named: dict[str, set[str]] = {}
    for row in _table_rows():
        verb, subverbs, _, _ = _row_command(row)
        named.setdefault(verb, set()).update(subverbs)
    missing = [v for v in sorted(choices) if v not in named]
    assert not missing, f"verbs missing from the README table: {missing}"
    for verb in sorted(FAMILIES):
        sub_choices = choices[verb]._subparsers._group_actions[0].choices
        absent = [s for s in sorted(sub_choices) if s not in named[verb]]
        assert not absent, f"{verb} subverbs missing from the table: {absent}"
