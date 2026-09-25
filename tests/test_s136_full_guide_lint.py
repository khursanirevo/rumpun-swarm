"""s136 w1: every rumpun command in the guide parses against the live parser.

The s121 pin lints the guide's ```shell fences; the s128 pin guards the
README verbs table. Commands outside shell fences still drift silently:
bare/text/yaml fences and the inline code spans in the guide's prose.
This pin lints every command in every guide section, fence or inline
span, and re-proves the README verbs table by re-running the s128 pin's
tests, so one guard cannot regress while the other is skipped.
"""

from __future__ import annotations

import importlib.util
import re
import shlex
from pathlib import Path

from rumpun import cli

REPO = Path(__file__).resolve().parents[1]
GUIDE = REPO / "docs" / "campaign-guide.md"
S128 = REPO / "tests" / "test_s128_readme_verbs_lint.py"
FAMILIES = {"season", "evolve", "plugin", "ledger"}


def _sections(text: str) -> list[tuple[str, str]]:
    """Split the guide into (section, body) pairs; the preamble is front matter."""
    parts = re.split(r"^(## .+)$", text, flags=re.MULTILINE)
    pairs = [("front matter", parts[0])] if parts[0].strip() else []
    heads = (h.strip("# ").strip() for h in parts[1::2])
    return pairs + list(zip(heads, parts[2::2], strict=True))


def _fence_commands(body: str) -> list[str]:
    out: list[str] = []
    for _tag, code in re.findall(r"```(\w*)\n(.*?)```", body, re.DOTALL):
        out.extend(
            line.strip()
            for line in code.replace("\\\n", " ").splitlines()
            if line.strip().startswith("rumpun ")
        )
    return out


def _inline_commands(body: str) -> list[str]:
    return [
        span.strip()
        for span in re.findall(r"`([^`\n]+)`", body)
        if span.strip().startswith("rumpun ")
    ]


def _commands(text: str) -> list[tuple[str, str]]:
    """Every rumpun command as (section, command) pairs."""
    return [
        (section, cmd)
        for section, body in _sections(text)
        for cmd in _fence_commands(body) + _inline_commands(body)
    ]


def _lint_one(cmd: str, choices: dict) -> str | None:
    """Return None when the command parses, else the drift reason."""
    try:
        tokens = shlex.split(cmd)
    except ValueError as exc:
        return f"shlex error: {exc}"
    if len(tokens) < 2:
        return "names no verb"
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


def test_guide_still_carries_commands_outside_shell_fences() -> None:
    """The extension is live: no commands means the pin guards nothing."""
    guide = GUIDE.read_text()
    total = _fence_commands(guide) + _inline_commands(guide)
    assert len(total) >= 20, f"guide carries {len(total)} commands; extraction looks broken"
    assert _inline_commands(guide), "no inline code-span commands; the extension covers nothing"


def test_new_lint_covers_every_s121_scope_command() -> None:
    """The s136 extraction is a superset of the s121 shell-fence scope."""
    guide = GUIDE.read_text()
    shell = [
        line.strip()
        for fence in re.findall(r"```shell\n(.*?)```", guide, re.DOTALL)
        for line in fence.replace("\\\n", " ").splitlines()
        if line.strip().startswith("rumpun ")
    ]
    assert shell, "the guide carries no shell-fenced commands"
    new = {cmd for _, cmd in _commands(guide)}
    missing = [cmd for cmd in shell if cmd not in new]
    assert not missing, f"the s136 lint dropped s121-scope commands: {missing}"


def test_every_command_in_every_section_parses() -> None:
    """Verb, subverb, and flags parse against the current parser leaf."""
    choices = cli.build_parser()._subparsers._group_actions[0].choices
    drift = []
    for section, cmd in _commands(GUIDE.read_text()):
        why = _lint_one(cmd, choices)
        if why:
            drift.append(f"[{section}] {cmd!r}: {why}")
    assert not drift, f"{len(drift)} guide command(s) drifted: " + "; ".join(drift)


def test_readme_verbs_table_reproven() -> None:
    """Re-run the s128 pin's two tests against the live README."""
    assert S128.is_file(), f"the s128 pin is gone: {S128}"
    spec = importlib.util.spec_from_file_location("_s136_s128", S128)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.test_every_table_row_lints_against_the_parser()
    module.test_every_parser_verb_has_a_table_row()
