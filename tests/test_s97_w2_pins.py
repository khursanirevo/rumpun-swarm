"""s97 w2 pins — the assessment composition's shape, the named refusals.

Spec source: the composer src/rumpun/audit.py (seal_usefulness_assessment,
_usefulness_front_line) and the sealed precedent
.rumpun/ledger/2026-09-17_usefulness-s87.md. The s88 w2 pins hold the
vocabulary and the CLI wiring with loose refusal matches; these hold what
the s97 w1 seal exercises, byte for byte and message for message: a
fixture front set composes to the s87 body shape, the optional-basis
front line is byte-shaped, and the composer's three torn-shape refusals
fire with their exact named messages. Offline: in-process over tmp_path
fixture roots; no subprocess, no route call, no network.

Contract these pins hold -- src/rumpun/audit.py:

1. A fixture front set composes to the s87 byte-shape: the verdict line,
   the basis line (the default pinned verbatim), `fronts:`, one front
   line per front (`- <name> - owner: <owner>. <basis> Next: <next>.`),
   the satisfied header, one bullet per satisfied line; the sealed
   sha256 digests exactly those body bytes; the reader reads the sealed
   record back field-identical.
2. The optional-basis branch is byte-shaped: a front with no basis
   composes `- <name> - owner: <owner>. Next: <next>.`, the body
   byte-stable at that arity.
3. An empty name refuses with the named message: `assessment front is
   missing name: ...`.
4. A name carrying ` - owner: ` refuses with the named message:
   `assessment front name carries the owner separator: ...`.
5. An owner carrying `. ` refuses with the named message:
   `assessment front owner carries '. ' (the basis would not read
   back): ...`.

Grafting: drop this file into tests/. Helpers and constants carry the
_s97w2_ prefix; nothing collides with existing defs.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from rumpun import audit as audit_mod

# Hardcoded (never imported): a regression pin that imported the live
# constant could not fail when the constant regresses.
_S97W2_DEFAULT_BASIS = (
    "directive seq 9 - usefulness exhaustion is the stopping criterion;"
    " every front below names its owner and next-action"
)

_S97W2_SATISFIED = [
    "the composition arc - the pinned shape sealed the s97 assessment",
]

# The fixture front set: two fronts, each with a basis clause, so the
# pin holds two front lines, not one.
_S97W2_FRONTS = [
    {
        "name": "the campaign ledger",
        "owner": "campaign (s97 w1, in flight)",
        "basis": "the board arc holds at twenty-one wins",
        "next": "w1 seals the s97 assessment through the composer",
    },
    {
        "name": "the open season",
        "owner": "operator",
        "basis": "the two views sum to the closed ledger",
        "next": "the operator seeds s98 from the closed ledger",
    },
]


def _s97w2_refuses(root: Path, front: dict[str, str], message: str) -> None:
    """One front in, AuditError with the exact message out, nothing lands."""
    with pytest.raises(audit_mod.AuditError) as excinfo:
        audit_mod.seal_usefulness_assessment(root, "s97fx", "CONTINUE", [front])
    assert str(excinfo.value) == message
    assert not (root / "ledger").exists() or not any((root / "ledger").iterdir())


def test_s97w2_front_set_composes_s87_byte_shape(tmp_path: Path) -> None:
    """Fronts in, the s87 body shape out byte for byte; the sha digests
    the body; the reader reads the sealed record back field-identical."""
    root = tmp_path / "s97w2ledger"
    path = audit_mod.seal_usefulness_assessment(
        root, "s97fx", "CONTINUE", _S97W2_FRONTS, satisfied=_S97W2_SATISFIED,
    )
    lines = path.read_text(encoding="utf-8").splitlines()
    front_one = (
        "- the campaign ledger - owner: campaign (s97 w1, in flight)."
        " the board arc holds at twenty-one wins"
        " Next: w1 seals the s97 assessment through the composer."
    )
    front_two = (
        "- the open season - owner: operator."
        " the two views sum to the closed ledger"
        " Next: the operator seeds s98 from the closed ledger."
    )
    expected_body = "\n".join(
        [
            "verdict: CONTINUE",
            f"basis: {_S97W2_DEFAULT_BASIS}",
            "fronts:",
            front_one,
            front_two,
            "satisfied (recorded, not fronts):",
            "- the composition arc - the pinned shape sealed the s97 assessment",
        ]
    )
    assert "\n".join(lines[4:-1]) == expected_body
    assert lines[1] == "id: usefulness-s97fx"
    assert lines[3] == (
        "title: CONTINUE (the per-season usefulness assessment over the whole ledger)"
    )
    assert lines[-1] == (
        f"sha256: {hashlib.sha256(expected_body.encode('utf-8')).hexdigest()}"
    )
    data = audit_mod.read_usefulness_assessment(path)
    assert data["verdict"] == "CONTINUE"
    assert data["basis"] == _S97W2_DEFAULT_BASIS
    assert data["fronts"] == _S97W2_FRONTS
    assert data["satisfied"] == _S97W2_SATISFIED


def test_s97w2_no_basis_front_is_byte_shaped(tmp_path: Path) -> None:
    """A front with no basis composes the short line; the body stays
    byte-stable at that arity, the satisfied header still closing it."""
    root = tmp_path / "s97w2shortline"
    path = audit_mod.seal_usefulness_assessment(
        root, "s97fy", "CONTINUE", [
            {
                "name": "the open season",
                "owner": "operator",
                "basis": "",
                "next": "the operator seeds s98 from the closed ledger",
            },
        ],
    )
    body = "\n".join(path.read_text(encoding="utf-8").splitlines()[4:-1])
    assert body == (
        "verdict: CONTINUE\n"
        f"basis: {_S97W2_DEFAULT_BASIS}\n"
        "fronts:\n"
        "- the open season - owner: operator."
        " Next: the operator seeds s98 from the closed ledger.\n"
        "satisfied (recorded, not fronts):"
    )


def test_s97w2_empty_name_refuses_with_named_message(tmp_path: Path) -> None:
    """The empty-name refusal names the missing field and the front."""
    _s97w2_refuses(
        tmp_path / "s97w2refuse",
        {"name": "", "owner": "o", "next": "x"},
        "assessment front is missing name: {'name': '', 'owner': 'o', 'next': 'x'}",
    )


def test_s97w2_name_owner_separator_refuses_with_named_message(tmp_path: Path) -> None:
    """The name-side owner-separator collision refuses, message named."""
    _s97w2_refuses(
        tmp_path / "s97w2refuse",
        {"name": "a - owner: b", "owner": "o", "next": "x"},
        "assessment front name carries the owner separator: 'a - owner: b'",
    )


def test_s97w2_owner_dot_refuses_with_named_message(tmp_path: Path) -> None:
    """The owner-side '. ' separator refuses: the basis would not read back."""
    _s97w2_refuses(
        tmp_path / "s97w2refuse",
        {"name": "n", "owner": "o. x", "next": "x"},
        "assessment front owner carries '. ' (the basis would not read back): 'o. x'",
    )
