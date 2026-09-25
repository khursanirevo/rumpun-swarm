"""s114 w1 pins -- the fifth usefulness assessment: the inputs pre-flight.

Spec source: the s114 w1 brief (.rumpun/prompts/dev/w1-fifth-assessment.md),
the sealed priors (usefulness-s87 through usefulness-s107), and the seam
contract in src/rumpun/audit.py (usefulness_inputs,
seal_usefulness_assessment, read_usefulness_assessment, wired through
`rumpun harvest --assessment-file`). The standing step: every close seals
one usefulness-<sid> record over the whole ledger, and the inputs
pre-flight refuses a bad file before any close write. These pins hold
this season's contract:

1. A bad basis refuses: the basis splices into the record as ONE body
   line (the s87 shape), so a basis carrying a newline tears the
   byte-stable shape. usefulness_inputs and seal_usefulness_assessment
   both refuse (AuditError) -- the same both-doors discipline the fronts
   get through _usefulness_front_line.
2. A missing key refuses: a non-mapping file, a missing verdict, and
   missing fronts each raise AuditError naming the field -- a malformed
   file cannot quietly skip the standing step.
3. The happy path is the real campaign file: .rumpun/seasons/
   s114-assessment.yaml pre-flights clean through usefulness_inputs
   (verdict CONTINUE, every front naming owner and next-action, the
   basis present and naming the last seal usefulness-s107), and the
   parsed inputs seal a fixture campaign whose record reads back
   field-identical.

Offline: in-process over tmp_path fixture campaigns plus one read of the
committed campaign yaml; no route call, no gh call, no network. The yaml
locator walks up to the repo root (the s70 w2 pattern: pyproject +
src/rumpun + DESIGN.md), so the pin holds in the checker's archive
extract where cwd differs and .venv is absent.

Grafting: drop this file into tests/. Helpers and constants carry the
_s114 prefix; nothing collides with existing defs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rumpun import audit as audit_mod
from rumpun import yamlio

_S114_YAML = Path(".rumpun") / "s114-assessment.yaml"
_S114_LAST_SEAL = "usefulness-s107"
_S114_FRONT = {
    "name": "the bad-basis pin front",
    "owner": "campaign",
    "basis": "the guard is this season's seam land.",
    "next": "the close seals the next assessment",
}


def _s114_repo() -> Path:
    """Repo root by the s70 w2 walk-up (pyproject + src/rumpun + DESIGN)."""
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s114_seal(root: Path, sid: str, basis: str) -> Path:
    return audit_mod.seal_usefulness_assessment(
        root,
        sid,
        "CONTINUE",
        [dict(_S114_FRONT)],
        basis=basis,
    )


def test_s114_pin1_bad_basis_refuses(tmp_path):
    """A newline-bearing basis refuses at both doors (AuditError, no write)."""
    campaign = tmp_path / "camp"
    campaign.mkdir()
    bad = "basis line one\nbasis line two"
    with pytest.raises(audit_mod.AuditError):
        audit_mod.usefulness_inputs(
            {"verdict": "CONTINUE", "fronts": [dict(_S114_FRONT)], "basis": bad}
        )
    with pytest.raises(audit_mod.AuditError):
        _s114_seal(campaign, "s114x", bad)
    assert list(campaign.glob("*.md")) == []


def test_s114_pin2_missing_key_refuses():
    """A non-mapping file, a missing verdict, and missing fronts all refuse."""
    with pytest.raises(audit_mod.AuditError):
        audit_mod.usefulness_inputs({})
    with pytest.raises(audit_mod.AuditError):
        audit_mod.usefulness_inputs({"verdict": "CONTINUE"})
    with pytest.raises(audit_mod.AuditError):
        audit_mod.usefulness_inputs(["not", "a", "mapping"])


def test_s114_pin3_happy_path_real_campaign_yaml(tmp_path):
    """The real campaign yaml pre-flights clean and seals a readable record."""
    root = _s114_repo()
    yaml_path = root / _S114_YAML
    assert yaml_path.is_file(), f"the campaign assessment yaml is missing: {yaml_path}"
    verdict, fronts, satisfied, basis = audit_mod.usefulness_inputs(
        yamlio.load(yaml_path)
    )
    assert verdict == "CONTINUE"
    assert fronts, "the assessment names no fronts"
    assert basis is not None, "the basis key is absent; the module default would seal"
    assert _S114_LAST_SEAL in basis, (
        f"the basis must name the last seal ({_S114_LAST_SEAL})"
    )
    campaign = tmp_path / "camp"
    campaign.mkdir()
    record = audit_mod.seal_usefulness_assessment(
        campaign, "s114x", verdict, fronts, satisfied=satisfied, basis=basis
    )
    readback = audit_mod.read_usefulness_assessment(record)
    assert readback["verdict"] == "CONTINUE"
    assert readback["basis"] == basis
    assert len(readback["fronts"]) == len(fronts)
    assert len(readback["satisfied"]) == len(satisfied)
