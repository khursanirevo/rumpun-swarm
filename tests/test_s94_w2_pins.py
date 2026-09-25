"""s94 w2 pins — the cost-accounting contract and the spend-line shape.

Spec source: the w2 prompt and board issue #18 (the audit-46 cost
residual). The kancil-base draft pack carries the contract as
priors/templates/cost-accounting.md; the manifest seal is asserted
against a live recompute (the s46w2/s81 three-way convention:
declared == repo fn == independent), never a pinned literal, so
sibling templates can land without breaking these pins. All pins are
offline and in-process: no route call, no network, no pack mutation.

Contract these pins hold:

1. The template exists in the draft pack, names its residual issue,
   and carries the three honestly-measurable quantities plus the
   three unmeasurable columns.
2. The spend-line shape in the template's skeleton is the shape the
   reference renderer emits (template and renderer cannot drift).
3. A fixture harvest record parses to one spend line derived from
   the writer table only; no unrecorded column can enter it.
4. The honesty caption and the closing rule stay in the template.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import yaml

from rumpun import plugin as plugin_mod

logger = logging.getLogger(__name__)

S94W2_PACK = Path(
    "/mnt/data/work/rumpun/.rumpun/plugins/kancil-base-draft"
)
S94W2_TEMPLATE = S94W2_PACK / "priors" / "templates" / "cost-accounting.md"

S94W2_SPEND_LINE = (
    "spend: writers=<n> writer_seconds=<sum> duration_s=<season duration>"
)
S94W2_CAPTION = (
    "The table proves nothing alone: seconds are not money, and the "
    "unrecorded columns (tokens, API cost, operator time) stay invisible."
)
S94W2_MEASURABLE = (
    "writer-seconds per season",
    "seasons per week",
    "filed-to-closed elapsed times",
)
S94W2_UNMEASURABLE = ("token counts", "api cost", "manual-time counterweight")


def _s94w2_template_text() -> str:
    """The sealed template, read as text."""
    return S94W2_TEMPLATE.read_text(encoding="utf-8")


def _s94w2_normalized(text: str) -> str:
    """Whitespace-normalized text, so wrapped lines match verbatim."""
    return " ".join(text.split()).casefold()


def _s94w2_independent_digest(pack: Path) -> str:
    """The declared v1 digest, recomputed without repo helpers."""
    digest = hashlib.sha256()
    priors = pack / "priors"
    for path in sorted(p for p in priors.rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _s94w2_spend_line(writers: int, writer_seconds: float, duration: int) -> str:
    """The reference renderer: the template skeleton's one-line shape."""
    return (
        f"spend: writers={writers} "
        f"writer_seconds={writer_seconds:.1f} "
        f"duration_s={duration}"
    )


def _s94w2_fixture_record() -> str:
    """One harvest record with the campaign's writer-table schema."""
    return (
        "# akar record: sN-harvest\n"
        "id: sN-harvest\n"
        "date: 2026-09-18\n"
        "title: season sN harvest\n"
        "season sN: completed\n"
        "duration: 1544s\n"
        "\n"
        "| agent | route | state | exit_code | seconds |\n"
        "|---|---|---|---|---|\n"
        "| w1 | fable | exited | 0 | 1543.5 |\n"
        "| w2 | fable | exited | 0 | 1543.5 |\n"
        "\n"
        "verdict: WIN\n"
    )


def _s94w2_declared_digest() -> str:
    """The manifest's digest line, read as text (no yaml round-trip)."""
    manifest = (S94W2_PACK / "manifest.yaml").read_text(encoding="utf-8")
    for line in manifest.splitlines():
        if line.startswith("digest:"):
            return line.split(":", 1)[1].strip()
    msg = "manifest carries no digest line"
    raise ValueError(msg)


def test_s94w2_template_sealed_three_way() -> None:
    """Declared == repo fn == independent recompute over the priors."""
    declared = _s94w2_declared_digest()
    assert declared == plugin_mod.priors_digest(S94W2_PACK)
    assert declared == _s94w2_independent_digest(S94W2_PACK)


def test_s94w2_pack_lint_has_no_errors() -> None:
    """The publish gate stays clean with the contract in the tree."""
    manifest_text = (S94W2_PACK / "manifest.yaml").read_text(
        encoding="utf-8"
    )
    manifest = yaml.safe_load(manifest_text)
    findings = plugin_mod.plugin_lint(S94W2_PACK, manifest)
    errors = [f for f in findings if f.severity == "error"]
    assert errors == []


def test_s94w2_template_names_the_contract() -> None:
    """The template names its residual issue, quantities, and columns."""
    text = _s94w2_normalized(_s94w2_template_text())
    assert "issue #18" in text
    for phrase in S94W2_MEASURABLE:
        assert phrase in text
    for phrase in S94W2_UNMEASURABLE:
        assert phrase in text


def _s94w2_parse_seconds(record_text: str) -> tuple[int, float]:
    """Sum the seconds column of the writer table only."""
    seconds = [
        float(line.rsplit("|", 2)[-2].strip())
        for line in record_text.splitlines()
        if line.startswith("| w")
    ]
    return len(seconds), round(sum(seconds), 1)


def test_s94w2_spend_line_shape_matches_template() -> None:
    """The skeleton line and the reference renderer are one shape."""
    assert S94W2_SPEND_LINE in _s94w2_template_text()
    assert _s94w2_spend_line(2, 3087.0, 1544) == (
        "spend: writers=2 writer_seconds=3087.0 duration_s=1544"
    )


def test_s94w2_fixture_parses_to_spend_line() -> None:
    """One fixture record parses to the (writers, seconds) pair."""
    writers, seconds = _s94w2_parse_seconds(_s94w2_fixture_record())
    assert writers == 2
    assert seconds == 3087.0
    assert _s94w2_spend_line(writers, seconds, 1544) == (
        "spend: writers=2 writer_seconds=3087.0 duration_s=1544"
    )


def test_s94w2_spend_line_ignores_unrecorded_columns() -> None:
    """Token, cost, and manual columns cannot enter the spend line."""
    poisoned = _s94w2_fixture_record().replace(
        "verdict: WIN",
        "tokens: 999999\napi_cost: 42.0\noperator_minutes: 90\nverdict: WIN",
    )
    writers, seconds = _s94w2_parse_seconds(poisoned)
    assert (writers, seconds) == (2, 3087.0)


def test_s94w2_honesty_caption_and_closing_rule() -> None:
    """The caption and the stay-open rule survive verbatim."""
    text = _s94w2_normalized(_s94w2_template_text())
    assert S94W2_CAPTION.casefold() in text
    assert "stays open until a spend line lands in the harvest schema" in text
