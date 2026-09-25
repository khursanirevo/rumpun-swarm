"""s121 w2: docs/campaign-guide.md stays parseable against the CLI parser.

Every ```shell fence line that starts with `rumpun ` must name a verb (and
subverb, for the season/evolve/plugin/ledger families) the parser accepts,
and every --flag on the line must be a known option of that subparser.
Non-rumpun lines (git, and prose mentions outside fences) are out of scope.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

from rumpun import cli

REPO = Path(__file__).resolve().parents[1]
GUIDE = REPO / "docs" / "campaign-guide.md"
README = REPO / "README.md"
FAMILIES = {"season", "evolve", "plugin", "ledger"}


def _shell_fences(text: str) -> list[str]:
    return re.findall(r"```shell\n(.*?)```", text, re.DOTALL)


def _rumpun_commands(fence: str) -> list[str]:
    joined = fence.replace("\\\n", " ")
    return [
        line.strip()
        for line in joined.splitlines()
        if line.strip().startswith("rumpun ")
    ]


def _leaf_parser(choices: dict, tokens: list[str], cmd: str):
    verb = tokens[1]
    assert verb in choices, f"{cmd!r}: unknown verb {verb!r}"
    leaf = choices[verb]
    if verb in FAMILIES:
        assert leaf._subparsers is not None, f"{cmd!r}: {verb} has no subverbs"
        sub_choices = leaf._subparsers._group_actions[0].choices
        assert len(tokens) > 2 and tokens[2] in sub_choices, (
            f"{cmd!r}: unknown {verb} subverb"
        )
        leaf = sub_choices[tokens[2]]
    return leaf


def test_guide_exists_and_readme_links_it() -> None:
    assert GUIDE.is_file()
    assert "docs/campaign-guide.md" in README.read_text()


def test_every_rumpun_command_names_a_real_verb_and_flags() -> None:
    text = GUIDE.read_text()
    commands = [
        cmd for fence in _shell_fences(text) for cmd in _rumpun_commands(fence)
    ]
    assert commands, "the guide carries no shell-fenced rumpun commands"
    parser = cli.build_parser()
    choices = parser._subparsers._group_actions[0].choices
    for cmd in commands:
        tokens = shlex.split(cmd)
        leaf = _leaf_parser(choices, tokens, cmd)
        known = {
            opt for action in leaf._actions for opt in action.option_strings
        }
        unknown = [t for t in tokens if t.startswith("--") and t not in known]
        assert not unknown, f"{cmd!r}: unknown flags {unknown}"
