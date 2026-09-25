"""s128 w2 pins — the guide's models section documents the --write re-detect.

The s126 verb taught `models --write` to re-read filled campaigns: the
diff, the named additions, the never-clobber rule, the idempotence
(src/rumpun/routes.py redetect_routes, pinned by
tests/test_s126_models_redetect.py). The guide's models paragraph
predates the verb and says nothing about what a filled campaign gets.
These pins hold the section to the s126 behavior, measured 2026-09-20.

Section anchor: the span between the "Detect the model routes" opener and
the "Edit two files" opener. The s121 command-lint guard already checks
every guide fence against the parser, and this section gains no new
commands (pinned here: the span's only fence stays the models verb), so
the lint extension is a no-op by design.

Grafting: drop into tests/. Helpers carry the _s128 prefix, no def
collides with the existing suite.
"""

from __future__ import annotations

import re
from pathlib import Path

from rumpun import cli

REPO = Path(__file__).resolve().parents[1]
GUIDE = REPO / "docs" / "campaign-guide.md"

MODELS_START = "Detect the model routes"
MODELS_END = "Edit two files before the first lint"


def _s128_models_span() -> str:
    """Guide text from the models paragraph opener to the next paragraph
    opener, stable to prose edits inside the span."""
    lines = GUIDE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith(MODELS_START))
    end = next(
        i for i, ln in enumerate(lines) if i > start and ln.startswith(MODELS_END)
    )
    return "\n".join(lines[start:end])


def test_s128w2_section_keeps_the_write_verb_fence() -> None:
    """The section stays anchored to the verb: one shell fence, it runs
    `rumpun models --write`, and the parser accepts the verb (the s121
    guard lints the flags)."""
    span = _s128_models_span()
    fences = re.findall(r"```shell\n(.*?)```", span, re.DOTALL)
    assert len(fences) == 1
    assert "rumpun models --write" in fences[0]
    choices = cli.build_parser()._subparsers._group_actions[0].choices
    assert "models" in choices


def test_s128w2_section_documents_the_redetect_facts() -> None:
    """What a filled campaign gets, matching the s126 verb exactly. Each
    fact pinned on the words that state it: the diff, the named
    additions, the never-clobber rule, the idempotence, and the refusal
    when no routes block exists."""
    span = _s128_models_span().lower()
    # the diff: --write re-detects and diffs against the filled block
    assert re.search(r"re-detect|redetect", span), "no re-detect statement"
    assert re.search(r"\bdiff", span), "no diff statement"
    # the named additions: only newly detected keys land
    assert "newly detected" in span, "no named-additions statement"
    # the never-clobber rule: existing lines stay byte-untouched
    assert re.search(r"byte-untouched|never clobber", span), (
        "no never-clobber statement"
    )
    # the idempotence: a second run finds no new keys, writes nothing
    assert "second run" in span, "no idempotence statement"
    assert re.search(r"nothing|no new", span), "no idempotence statement"
    # the refusal: no routes block at all leaves the file untouched
    assert re.search(r"refusal|refuses", span), "no refusal statement"
