"""s105 w2 pins -- the assessment basis-superseding convention.

Spec source: the s104 w1 disclosed miss (.rumpun/runs/s104/w1/notes.md --
the assessment yaml omitted the top-level basis key, the record carries the
module's default basis, and sealed records never delete) and the s105 w2
brief (.rumpun/runs/s105/w2/prompt.md). The akar discipline: sealed records
never delete, so a wrong basis is corrected by append. The convention:

- a superseding re-seal refuses an unchanged basis (no noise) and
  otherwise appends usefulness-<sid>-basis -- a full assessment record
  whose basis line is the correction and whose supersedes line cites the
  original id and body sha256; the original stands byte-identical;
- read_usefulness_assessment returns the superseding basis when the
  record has one, naming it in basis_superseded_by.

Contract these pins hold -- src/rumpun/audit.py
(seal_usefulness_assessment's supersede half + read_usefulness_assessment):

1. The re-seal appends: usefulness-<sid>-basis lands beside the original;
   the original file is byte-identical before and after; the supersede
   record reads back whole (verdict, fronts, satisfied) and its supersedes
   line cites the original id plus the original body digest; the title
   cites the original too.
2. The read prefers the superseding basis: the original reads back with
   the corrected basis and basis_superseded_by naming the superseding
   record; the supersede record reads back with its own basis and no
   basis_superseded_by; a record with no supersede sibling reads with its
   own basis.
3. A re-seal without a basis change refuses (no noise): an unchanged
   explicit basis and an unchanged default basis each raise AuditError
   and the ledger gains no file.
4. A supersede without an original refuses: the citation needs its
   target; the ledger gains no file.

Offline: every pin is in-process over a tmp_path campaign (akar's ledger
dir is created on append; no route call, no gh call, no network, no live
ledger -- the pins seal fixtures only).

Grafting: drop this file into tests/. Helpers and constants carry the
_s105w2_ prefix; nothing collides with existing defs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rumpun import audit as audit_mod
from rumpun import paths

_S105W2_ORIG_BASIS = "pin basis one (the s104 default-basis miss, replayed)"
_S105W2_FIXED_BASIS = "the corrected basis: the pause-and-go lives here (s105 w2 pin)"
_S105W2_FRONT = {
    "name": "the basis supersede pin",
    "owner": "campaign",
    "basis": "the convention lands in s105 w2.",
    "next": "the close seals the next assessment",
}
_S105W2_SATISFIED = ["the s104 w1 record stands; this is the correction path"]


def _s105w2_seal(
    root: Path, sid: str, *, basis: str | None = None, supersede: bool = False
) -> Path:
    return audit_mod.seal_usefulness_assessment(
        root,
        sid,
        "CONTINUE",
        [dict(_S105W2_FRONT)],
        satisfied=list(_S105W2_SATISFIED),
        basis=basis,
        supersede=supersede,
    )


def _s105w2_ledger_files(root: Path) -> list[str]:
    ledger = paths.ledger_dir(root)
    if not ledger.is_dir():
        return []
    return sorted(p.name for p in ledger.glob("*.md"))


def _s105w2_body(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[4:-1])


def _s105w2_digest(path: Path) -> str:
    return path.read_text(encoding="utf-8").splitlines()[-1].removeprefix("sha256: ")


def test_s105w2_pin1_supersede_appends_citing_the_original(tmp_path):
    campaign = tmp_path / "camp"
    campaign.mkdir()
    original = _s105w2_seal(campaign, "s105x", basis=_S105W2_ORIG_BASIS)
    before = original.read_bytes()
    supersede = _s105w2_seal(campaign, "s105x", basis=_S105W2_FIXED_BASIS, supersede=True)
    assert original.read_bytes() == before
    assert supersede.name.endswith("_usefulness-s105x-basis.md")
    cited = f"supersedes: usefulness-s105x (sha256 {_s105w2_digest(original)})"
    assert cited in _s105w2_body(supersede)
    assert len(_s105w2_ledger_files(campaign)) == 2
    data = audit_mod.read_usefulness_assessment(supersede)
    assert data["id"] == "usefulness-s105x-basis"
    assert data["verdict"] == "CONTINUE"
    assert data["basis"] == _S105W2_FIXED_BASIS
    assert data["fronts"] == [_S105W2_FRONT]
    assert data["satisfied"] == _S105W2_SATISFIED
    assert "the basis supersede of usefulness-s105x" in data["title"]


def test_s105w2_pin2_read_prefers_the_superseding_basis(tmp_path):
    campaign = tmp_path / "camp"
    campaign.mkdir()
    original = _s105w2_seal(campaign, "s105x", basis=_S105W2_ORIG_BASIS)
    control = _s105w2_seal(campaign, "s105y", basis="the control basis")
    supersede = _s105w2_seal(campaign, "s105x", basis=_S105W2_FIXED_BASIS, supersede=True)

    data = audit_mod.read_usefulness_assessment(original)
    assert data["basis"] == _S105W2_FIXED_BASIS
    assert data["basis_superseded_by"] == "usefulness-s105x-basis"
    assert data["verdict"] == "CONTINUE"

    data = audit_mod.read_usefulness_assessment(supersede)
    assert data["basis"] == _S105W2_FIXED_BASIS
    assert "basis_superseded_by" not in data

    data = audit_mod.read_usefulness_assessment(control)
    assert data["basis"] == "the control basis"
    assert "basis_superseded_by" not in data


def test_s105w2_pin3_unchanged_basis_refuses_without_noise(tmp_path):
    campaign = tmp_path / "camp"
    campaign.mkdir()
    original = _s105w2_seal(campaign, "s105x", basis="the unchanged basis")
    count = len(_s105w2_ledger_files(campaign))
    with pytest.raises(audit_mod.AuditError, match="basis unchanged"):
        _s105w2_seal(campaign, "s105x", basis="the unchanged basis", supersede=True)
    assert len(_s105w2_ledger_files(campaign)) == count

    _s105w2_seal(campaign, "s105z")
    assert len(_s105w2_ledger_files(campaign)) == count + 1
    with pytest.raises(audit_mod.AuditError, match="basis unchanged"):
        _s105w2_seal(campaign, "s105z", supersede=True)
    assert len(_s105w2_ledger_files(campaign)) == count + 1
    assert audit_mod.read_usefulness_assessment(original)["basis"] == "the unchanged basis"


def test_s105w2_pin4_supersede_without_an_original_refuses(tmp_path):
    campaign = tmp_path / "camp"
    campaign.mkdir()
    with pytest.raises(audit_mod.AuditError, match="cannot supersede"):
        _s105w2_seal(campaign, "s105x", basis="any basis", supersede=True)
    assert _s105w2_ledger_files(campaign) == []
