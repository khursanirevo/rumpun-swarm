"""s140 w1 pins -- the eleventh usefulness assessment: the inputs pre-flight.

Spec source: the s140 w1 brief (.rumpun/prompts/dev/w1-eleventh-assessment.md),
the sealed priors (usefulness-s87 through usefulness-s133 plus the
usefulness-s133-basis supersede), and the seam contract in src/rumpun/audit.py
(usefulness_inputs, seal_usefulness_assessment, read_usefulness_assessment,
wired through `rumpun harvest --assessment-file`). The standing step: the s140
close seals usefulness-s140 beside the harvest from
.rumpun/s140-assessment.yaml, the s88 door with the inputs pre-flighting
before any close write. The record shape is unchanged from the tenth seal,
so these pins hold this season's contract only:

1. A bad basis refuses: the basis splices into the record as ONE body line
   (the s87 shape), so a basis carrying a newline tears the byte-stable
   shape. usefulness_inputs and seal_usefulness_assessment both refuse
   (AuditError) -- the same both-doors discipline the fronts get through
   _usefulness_front_line.
2. A missing key refuses: a non-mapping file, a missing verdict, and
   missing fronts each raise AuditError naming the field -- a malformed
   file cannot quietly skip the standing step.
3. The happy path is the real campaign file: .rumpun/s140-assessment.yaml
   pre-flights clean through usefulness_inputs (verdict CONTINUE, six
   fronts, every front naming owner and next-action, the basis present and
   naming the last seal usefulness-s133), and the parsed inputs seal a
   fixture campaign whose record reads back field-identical.
4. The close-door seal derives the epics counts from the campaign it is
   handed: a fixture campaign with a minimal epics.yaml and one member's
   run state seals a record whose epics row renders the member's raw
   counts, the clause the brief demands in the record body.

Fixture discipline: in-process over tmp_path fixture campaigns plus one
read of the committed campaign yaml; no route call, no gh call, no
network; the real ledger is never written. The yaml locator walks up to
the repo root (the s70 w2 pattern: pyproject + src/rumpun + DESIGN.md),
so the pin holds in the checker's archive extract where cwd differs and
.venv is absent.

Grafting: drop this file into tests/. Helpers and constants carry the
_s140 prefix; nothing collides with existing defs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rumpun import audit as audit_mod
from rumpun import yamlio

_S140_YAML = Path(".rumpun") / "s140-assessment.yaml"
_S140_LAST_SEAL = "usefulness-s133"
_S140_FRONT_COUNT = 6
_S140_FRONT = {
    "name": "the eleventh assessment front",
    "owner": "campaign",
    "basis": "the counts row renders beside the raw ones",
    "next": "the close seals the next assessment",
}


def _s140_repo() -> Path:
    """Repo root by the s70 w2 walk-up (pyproject + src/rumpun + DESIGN)."""
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s140_fx(root: Path, *, with_epics: bool) -> Path:
    """A minimal fixture campaign: a ledger dir, one member's run state
    with a WIN verdict row, and optionally a one-epic epics.yaml declaring
    it. The state/verdict shapes mirror the s118 fixture constants."""
    (root / "ledger").mkdir(parents=True)
    member = root / "runs" / "s140fx"
    (member / "_season").mkdir(parents=True)
    (member / "_season" / "state.json").write_text(
        json.dumps({"id": "s140fx", "status": "completed"}), encoding="utf-8"
    )
    (member / "verdicts.jsonl").write_text(
        '{"season": "s140fx", "verdict": "WIN"}\n', encoding="utf-8"
    )
    if with_epics:
        (root / "epics.yaml").write_text(
            "one-epic:\n"
            "  title: the counts derive at seal time\n"
            "  goal: the body carries the adjusted counts\n"
            "  seasons:\n"
            "  - s140fx\n",
            encoding="utf-8",
        )
    return root


def _s140_seal(root: Path, verdict: str, fronts: list[dict[str, str]], *, satisfied=(), basis=None):
    """The seal under test: the campaign root is the .rumpun dir."""
    return audit_mod.seal_usefulness_assessment(
        root, "s140fx", verdict, fronts, satisfied=satisfied, basis=basis
    )


def test_s140_pin1_bad_basis_refuses(tmp_path):
    """A newline-bearing basis refuses at both doors (AuditError, no write)."""
    campaign = tmp_path / "camp"
    campaign.mkdir()
    bad = "basis line one\nbasis line two"
    with pytest.raises(audit_mod.AuditError):
        audit_mod.usefulness_inputs(
            {"verdict": "CONTINUE", "fronts": [dict(_S140_FRONT)], "basis": bad}
        )
    with pytest.raises(audit_mod.AuditError):
        _s140_seal(campaign, "CONTINUE", [dict(_S140_FRONT)], basis=bad)
    assert list(campaign.glob("*.md")) == []


def test_s140_pin2_missing_key_refuses():
    """A non-mapping file, a missing verdict, and missing fronts all refuse."""
    with pytest.raises(audit_mod.AuditError):
        audit_mod.usefulness_inputs({})
    with pytest.raises(audit_mod.AuditError):
        audit_mod.usefulness_inputs({"verdict": "CONTINUE"})
    with pytest.raises(audit_mod.AuditError):
        audit_mod.usefulness_inputs(["not", "a", "mapping"])


def test_s140_pin3_happy_path_real_campaign_yaml(tmp_path):
    """The real campaign yaml pre-flights clean and seals a readable record."""
    root = _s140_repo()
    yaml_path = root / _S140_YAML
    assert yaml_path.is_file(), f"the campaign assessment yaml is missing: {yaml_path}"
    verdict, fronts, satisfied, basis = audit_mod.usefulness_inputs(
        yamlio.load(yaml_path)
    )
    assert verdict == "CONTINUE"
    assert len(fronts) == _S140_FRONT_COUNT
    assert basis is not None, "the basis key is absent; the module default would seal"
    assert _S140_LAST_SEAL in basis, (
        f"the basis must name the last seal ({_S140_LAST_SEAL})"
    )
    for front in fronts:
        assert front["name"] and front["owner"] and front["next"], front
    campaign = tmp_path / "camp"
    campaign.mkdir()
    record = _s140_seal(campaign, verdict, fronts, satisfied=satisfied, basis=basis)
    readback = audit_mod.read_usefulness_assessment(record)
    assert readback["verdict"] == "CONTINUE"
    assert readback["basis"] == basis
    assert len(readback["fronts"]) == _S140_FRONT_COUNT
    assert len(readback["satisfied"]) == len(satisfied)


def test_s140_pin4_seal_derives_epics_counts(tmp_path):
    """The close-door seal derives the epics counts from the campaign root."""
    root = _s140_fx(tmp_path / "campfx", with_epics=True)
    record = _s140_seal(root, "CONTINUE", [dict(_S140_FRONT)])
    body = "\n".join(record.read_text(encoding="utf-8").splitlines()[4:-1])
    rows = [line for line in body.splitlines() if line.startswith("- one-epic: ")]
    assert rows == ["- one-epic: 1 WIN / 0 LOSS / 0 other"], body
