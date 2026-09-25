"""s137 w2 pins: section 4 documents the steady-state mode.

The guide's keep-going section carries a "### The steady state" block:
the light-lane pattern (lint sweep, route probes, rehearsals), the
operator's decision gate, and the two ways out (a fresh candidate class
the operator approves, or the operator's word). These pins guard the
block: content assertions, a lint of every shell-fenced rumpun command
in the block against the live parser, and an exact command-set pin that
goes red first when a command is added, removed, or reworded. Reads
only the committed guide and the parser; no run-dir reads.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

from rumpun import cli

FAMILIES = {"season", "evolve", "plugin", "ledger"}

# The commands the steady-state block carries. The set pin fails on any
# addition, removal, or rewording; lint the newcomer, then extend.
EXPECTED_COMMANDS = frozenset(
    {
        "rumpun audit --last 10",
        "rumpun kanban",
        "rumpun resume",
        'rumpun direct "the steady state holds until I say otherwise"',
    }
)


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _steady_block() -> str:
    """The steady-state block body, up to the next '## ' heading."""
    guide = _repo_root() / "docs" / "campaign-guide.md"
    text = guide.read_text(encoding="utf-8")
    found = re.search(
        r"^### The steady state\n(.*?)(?=^## )", text, re.DOTALL | re.MULTILINE
    )
    assert found, "the guide lost its '### The steady state' block"
    return found.group(1)


def _block_commands(body: str) -> list[str]:
    """Every rumpun line in the body's fenced code blocks, stripped."""
    return [
        line.strip()
        for _tag, code in re.findall(r"```(\w*)\n(.*?)```", body, re.DOTALL)
        for line in code.replace("\\\n", " ").splitlines()
        if line.strip().startswith("rumpun ")
    ]


def _lint_one(cmd: str, choices: dict) -> str | None:
    """None when the command parses against the parser leaf, else why not."""
    try:
        tokens = shlex.split(cmd)
    except ValueError as exc:
        return f"shlex error: {exc}"
    if len(tokens) < 2 or tokens[0] != "rumpun":
        return "does not name the rumpun command"
    verb = tokens[1]
    if verb not in choices:
        return f"unknown verb {verb!r}"
    leaf = choices[verb]
    if verb in FAMILIES:
        if leaf._subparsers is None:
            return f"{verb} carries no subverbs"
        subs = leaf._subparsers._group_actions[0].choices
        if len(tokens) < 3 or tokens[2] not in subs:
            named = tokens[2] if len(tokens) > 2 else "nothing"
            return f"unknown {verb} subverb {named!r}"
        leaf = subs[tokens[2]]
    known = {opt for action in leaf._actions for opt in action.option_strings}
    unknown = [t for t in tokens[2:] if t.startswith("--") and t not in known]
    return f"unknown flags {unknown}" if unknown else None


def test_block_exists_with_both_fences() -> None:
    body = _steady_block()
    assert "steady state" in body
    assert body.count("```shell") >= 2
    assert len(_block_commands(body)) >= 4


def test_block_names_the_light_lanes() -> None:
    body = _steady_block()
    assert "lint sweep" in body
    assert "route probes" in body
    assert "rehearsals" in body
    assert "invents no work" in body


def test_block_names_the_decision_gate() -> None:
    assert "operator's decision gate" in _steady_block()


def test_block_names_both_exits() -> None:
    body = _steady_block()
    assert "fresh candidate class" in body
    assert "operator's word" in body
    assert "new season" in body


def test_block_commands_lint_against_the_parser() -> None:
    choices = cli.build_parser()._subparsers._group_actions[0].choices
    drift = []
    for cmd in _block_commands(_steady_block()):
        why = _lint_one(cmd, choices)
        if why:
            drift.append(f"{cmd!r}: {why}")
    assert not drift, f"{len(drift)} steady-state command(s) drifted: " + "; ".join(drift)


def test_block_command_set_is_pinned() -> None:
    got = set(_block_commands(_steady_block()))
    unexpected = got - EXPECTED_COMMANDS
    missing = EXPECTED_COMMANDS - got
    assert not unexpected and not missing, (
        f"unexpected: {sorted(unexpected)}; missing: {sorted(missing)}; "
        "lint any newcomer against the parser, then extend EXPECTED_COMMANDS"
    )


def test_added_command_turns_the_lint_and_set_pin_red() -> None:
    """Red-first: a doctored addition cannot pass the lint or the set pin."""
    choices = cli.build_parser()._subparsers._group_actions[0].choices
    doctored = _steady_block() + "\n```shell\nrumpun audit --lastten\n```\n"
    drift = [_lint_one(cmd, choices) for cmd in _block_commands(doctored)]
    assert any(drift), "the lint accepted a doctored command"
    assert set(_block_commands(doctored)) - EXPECTED_COMMANDS, (
        "the set pin missed an added command"
    )
