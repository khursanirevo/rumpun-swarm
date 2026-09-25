"""s147 w1 pins - the twelfth usefulness assessment: this season's contract.

Spec source: the s147 w1 brief, the sealed priors (usefulness-s87 through
usefulness-s140 plus usefulness-close, the EXHAUSTED seal), and the seam
contract in src/rumpun/audit.py (usefulness_inputs, seal_usefulness_assessment,
read_usefulness_assessment, wired through `rumpun harvest --assessment-file`).
The standing step: the s147 close seals usefulness-s147 beside the harvest from
.rumpun/s147-assessment.yaml (the s88 door; the seal is the close worker's per
the s140 precedent - the yaml composed by the lane, sealed through the module).
The record shape is unchanged from the eleventh seal, so these pins hold this
season's contract only:

1. The real campaign yaml pre-flights clean through usefulness_inputs
   (verdict CONTINUE, six fronts, every front naming owner and next-action,
   the basis present and naming the last seal usefulness-s140) and the parsed
   inputs seal a fixture campaign whose record reads back field-identical.
2. The citation gate: every ledger: token in the yaml (id@sha form and the
   audit-record filename form) resolves against the live ledger - id@sha
   pairs match the record's sha256 trailer, filename tokens exist, and the
   frontier citation ledger:usefulness-s140@... is among them.

Fixture discipline: in-process over the committed campaign yaml plus one tmp
fixture campaign; no route call, no gh call, no network; the real ledger is
never written (pin 2 reads it only). The yaml locator walks up to the repo
root (the s70 w2 walk-up: pyproject + src/rumpun/report.py + DESIGN.md), so
the pins hold in the checker's archive extract where cwd differs and .venv
is absent. Grafting: helpers and constants carry the _s147 prefix; nothing
collides with existing defs.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from rumpun import audit as audit_mod
from rumpun import yamlio

_S147_YAML = Path(".rumpun") / "s147-assessment.yaml"
_S147_LAST_SEAL = "usefulness-s140"
_S147_FRONT_COUNT = 6


def _s147_repo() -> Path:
    """Repo root by the s70 w2 walk-up (pyproject + src/rumpun + DESIGN)."""
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s147_ledger_index(ledger: Path) -> dict[str, str]:
    """{record id: sha256 trailer} over the committed ledger."""
    index: dict[str, str] = {}
    for f in ledger.glob("*.md"):
        body = f.read_text(encoding="utf-8")
        m_id = re.search(r"^id: (\S+)", body, re.M)
        m_sha = re.search(r"^sha256: ([0-9a-f]{64})\s*$", body, re.M)
        if m_id and m_sha:
            index[m_id.group(1)] = m_sha.group(1)
    return index


def test_s147_pin1_real_yaml_preflights_and_seals(tmp_path):
    """The real campaign yaml pre-flights clean and seals a readable record."""
    root = _s147_repo()
    yaml_path = root / _S147_YAML
    assert yaml_path.is_file(), f"the campaign assessment yaml is missing: {yaml_path}"
    verdict, fronts, satisfied, basis = audit_mod.usefulness_inputs(
        yamlio.load(yaml_path)
    )
    assert verdict == "CONTINUE"
    assert len(fronts) == _S147_FRONT_COUNT
    assert basis is not None, "the basis key is absent; the module default would seal"
    assert _S147_LAST_SEAL in basis, (
        f"the basis must name the last seal ({_S147_LAST_SEAL})"
    )
    for front in fronts:
        assert front["name"] and front["owner"] and front["next"], front
    campaign = tmp_path / "camp"
    campaign.mkdir()
    record = audit_mod.seal_usefulness_assessment(
        campaign, "s147", verdict, fronts, satisfied=satisfied, basis=basis
    )
    readback = audit_mod.read_usefulness_assessment(record)
    assert readback["verdict"] == "CONTINUE"
    assert readback["basis"] == basis
    assert len(readback["fronts"]) == _S147_FRONT_COUNT
    assert len(readback["satisfied"]) == len(satisfied)
    assert readback["epics"] == [], (
        "a fixture campaign without epics.yaml must seal the s88 shape"
    )


def test_s147_pin2_citations_resolve_against_live_ledger():
    """Every ledger: token in the yaml resolves against the live ledger."""
    root = _s147_repo()
    text = (root / _S147_YAML).read_text(encoding="utf-8")
    ledger = root / ".rumpun" / "ledger"
    id_sha = _s147_ledger_index(ledger)
    tokens = re.findall(r"ledger:([A-Za-z0-9_.@-]+)", text)
    assert len(tokens) >= 12, f"expected the full citation set, got {len(tokens)}"
    for tok in tokens:
        m = re.fullmatch(r"([A-Za-z0-9-]+)@([0-9a-f]{64})", tok)
        if m:
            rid, sha = m.groups()
            assert id_sha.get(rid) == sha, (
                f"citation {rid}@{sha[:8]} does not match the live ledger body"
            )
        else:
            assert tok.endswith(".md"), f"unrecognized ledger token form: {tok}"
            assert (ledger / tok).is_file(), f"ledger file token missing: {tok}"
    assert any(tok.startswith("usefulness-s140@") for tok in tokens), (
        "the frontier citation is missing"
    )
