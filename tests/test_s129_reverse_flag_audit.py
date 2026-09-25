"""s129 w1: the reverse flag audit - every parser flag named or hidden on purpose.

The s128 lane proved the forward direction: every table row parses against
the parser and every verb has a row. The reverse was left standing: a flag
the parser accepts can sit in no readme row, named by no footnote - silence,
the one state neither pin guards. The honest shape this pin enforces: a
parser flag is either named in its verb's table row or named in the
Verbs-section hide footnote (the prose carrying "intentionally hidden");
a flag in neither is drift, and the pin names it. The footnote carries the
argparse-standard --help/-h pair and the global --version, so no flag
class is exempt in code.

Fixture discipline: read-only pins against the live parser and README; no
writes anywhere.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 on the pre-audit tree, pin 1, naming the full
  silence: the four brief drifts (init --plugin, board --mirror,
  audit --dry-run, check --out-dir), the plugin trio (distill --source,
  publish --remote, pull --remote), the global --version, and the auto
  --help/-h pair; /tmp/s129-w1-pins-red.txt.
- GREEN captured 2026-09-20 after the README rows and the hide footnote
  landed; /tmp/s129-w1-pins-green.txt (the s129 pins plus the s128
  forward pin, 4 passed).
- Pin 2 is green on both sides by design: it guards the hide mechanism
  (no phantom hidden flags, no flag both hidden and row-named).
"""

from __future__ import annotations

import re
from pathlib import Path

from rumpun import cli

REPO = Path(__file__).resolve().parents[1]
README = REPO / "README.md"
FAMILIES = {"season", "evolve", "plugin", "ledger"}
VERBS_SECTION = re.compile(r"^## Verbs\n(.*?)(?=^## )", re.DOTALL | re.MULTILINE)
HIDDEN_MARKER = "intentionally hidden"


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


def _row_flags() -> dict[str, set[str]]:
    """verb -> the --flags its table rows name (family rows union)."""
    named: dict[str, set[str]] = {}
    for row in _table_rows():
        verb, _, flags, _ = _row_command(row)
        named.setdefault(verb, set()).update(flags)
    return named


def _hidden_flags() -> set[str]:
    """The hide footnote's flags; no footnote reads as an empty hide set."""
    block = VERBS_SECTION.search(README.read_text())
    assert block, "README.md carries no '## Verbs' section"
    prose = "\n".join(
        line
        for line in block.group(1).splitlines()
        if line.strip() and not line.startswith("|") and not line.startswith("#")
    )
    if HIDDEN_MARKER not in prose:
        return set()
    flags: set[str] = set()
    for span in re.findall(r"`([^`]*)`", prose):
        flags.update(tok for tok in span.split() if tok.startswith("-"))
    return flags


def _parser_flags() -> dict[str, set[str]]:
    """command path -> option strings: "rumpun" for the root, verb, "verb sub"."""
    parser = cli.build_parser()
    paths: dict[str, set[str]] = {"rumpun": set()}
    for action in parser._actions:
        paths["rumpun"].update(action.option_strings)
    choices = parser._subparsers._group_actions[0].choices
    for verb, leaf in choices.items():
        paths[verb] = set()
        for action in leaf._actions:
            paths[verb].update(action.option_strings)
        if verb in FAMILIES:
            sub_choices = leaf._subparsers._group_actions[0].choices
            for sub, sub_leaf in sub_choices.items():
                paths[f"{verb} {sub}"] = set()
                for action in sub_leaf._actions:
                    paths[f"{verb} {sub}"].update(action.option_strings)
    return paths


def test_every_parser_flag_is_named_or_hidden() -> None:
    """The parser cannot carry a flag its row and the footnote both skip."""
    hidden = _hidden_flags()
    named = _row_flags()
    drift: list[str] = []
    for path, flags in sorted(_parser_flags().items()):
        if path == "rumpun":
            # no global row exists; the hide footnote is the only row-less home
            drift += [f"rumpun {opt}" for opt in sorted(flags - hidden)]
            continue
        allowed = named.get(path.split()[0], set()) | hidden
        drift += [f"{path} {opt}" for opt in sorted(flags - allowed)]
    assert not drift, "flags named in neither their row nor the hide footnote: " + ", ".join(
        drift
    )


def test_the_hidden_set_is_exact() -> None:
    """The footnote hides only real parser flags and never row-named ones."""
    hidden = _hidden_flags()
    all_opts: set[str] = set()
    for flags in _parser_flags().values():
        all_opts.update(flags)
    phantom = sorted(hidden - all_opts)
    assert not phantom, f"the hide footnote names flags the parser lacks: {phantom}"
    row_named: set[str] = set()
    for flags in _row_flags().values():
        row_named.update(flags)
    dupes = sorted(hidden & row_named)
    assert not dupes, f"flags both hidden and row-named: {dupes}"
