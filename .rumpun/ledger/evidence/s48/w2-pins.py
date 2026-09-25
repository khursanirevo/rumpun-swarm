"""s48 w2 pins — the m5 repro re-seal: the M5 contract against the re-sealed
repro, and the audit-36 DRIFT arming verified honest.

Spec-first pins (red against current code) for the s48 contract: w1 owns the
repro's re-seal — the evidence script s22/w1-repro-m5.py (aka
repro_m5_failed_exit) asserts the M5 contract (a both-agents-fail season
maps to a nonzero exit with the honest "failed" status) and passes on
current main, so the audit's DRIFT row retires. These pins assert the M5
contract against the re-sealed repro and the honesty of the audit's DRIFT
classification. Spec, merge anchors, and the measured red set:
.rumpun/runs/s48/w2/notes.md.

Grafting: land this file in tests/ as-is (additions-only; existing suite
files stay untouched). Every helper carries the _s48w2_ prefix, so nothing
collides with existing defs.

Red today for the right reason: the evidence repro still carries the
pre-s23-era assumptions (rimba/ paths; a fixture season the P27 preflight
lint rejects before any agent spawns), so it crashes (exit 1) on current
main instead of passing — measured, see notes.md. After w1's re-seal lands
at the evidence path, both pins flip green without edits.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from rumpun import engine

_S48W2_REPRO = Path(".rumpun") / "ledger" / "evidence" / "s22" / "w1-repro-m5.py"


def _s48w2_repo_root() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and
    grafted into tests/ (post-graft): both sit under the repo root.
    """
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise AssertionError("no pyproject.toml ancestor: pins file not under the repo root")


def _s48w2_run_repro(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Run the evidence repro against current main src; capture both streams.

    The script resolves the repo from argv[1], inserts <repo>/src into
    sys.path for its own engine import, and passes <repo>/src as PYTHONPATH
    to every verb subprocess it spawns, so the run exercises current main
    regardless of the pin process's own import resolution.
    """
    repo = _s48w2_repo_root()
    repro = repo / _S48W2_REPRO
    assert repro.is_file(), f"m5 evidence repro missing: {repro}"
    return subprocess.run(
        [sys.executable, str(repro), str(repo)],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=str(tmp_path),
    )


def _s48w2_repro_signature(proc: subprocess.CompletedProcess[str]) -> str:
    """The repro's all-pass GREEN signature ("GREEN: N/N checks passed")."""
    combined = proc.stdout + proc.stderr
    matches = re.findall(r"GREEN: (\d+)/(\d+) checks passed", combined)
    return matches[-1] if matches else ""


def test_s48w2_resealed_repro_passes_with_m5_contract(tmp_path: Path) -> None:
    """s48 pin 1 (red today): the re-sealed repro passes the M5 contract on
    current main.

    The evidence repro is the M5 contract asserter: a both-agents-fail
    season maps to a nonzero exit with the honest "failed" status (parts
    A-C: finalize reclassification, the status -> exit-code mapping, and
    the end-to-end season verbs). The re-sealed repro must meet the matrix
    PASS bar — exit 0 plus the all-pass GREEN signature — and must still
    assert the honest "failed" status, so the re-seal cannot silently drop
    the contract.
    """
    source = (_s48w2_repo_root() / _S48W2_REPRO).read_text(encoding="utf-8")
    assert '"failed"' in source, (
        "the re-sealed repro must still assert the honest \"failed\" status"
    )
    proc = _s48w2_run_repro(tmp_path)
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"repro exited {proc.returncode}; tail:\n{combined[-1500:]}"
    signature = _s48w2_repro_signature(proc)
    assert signature, f"no all-pass GREEN signature in repro output:\n{combined[-1500:]}"
    passed, total = signature.split("/")
    assert passed == total, f"repro signature not all-pass: {signature}"


def test_s48w2_drift_row_retired_and_arming_honest(tmp_path: Path) -> None:
    """s48 pin 2 (red today): the audit-36 DRIFT row retires honestly.

    The audit armed this season with one DRIFT row (s22/w1-repro-m5.py,
    aka repro_m5_failed_exit): "assumptions moved", WIN band on re-seal.
    The classification was honest — current main really maps failed seasons
    to nonzero (engine.status_exit_code; the suite's own M5 pin
    test_season_all_agents_failed_maps_to_nonzero holds) — so the repro's
    red is moved assumptions, not a regression. Retirement is the matrix
    PASS bar: the repro exits 0 with the all-pass signature on current
    main.
    """
    records = sorted((_s48w2_repo_root() / ".rumpun" / "ledger").glob("*_audit-36.md"))
    assert records, "audit-36 record missing from the ledger"
    text = records[0].read_text(encoding="utf-8")
    assert "1 DRIFT" in text, "audit-36 corpus must record exactly one DRIFT"
    rows = [line for line in text.splitlines() if "s22/w1-repro-m5.py" in line]
    assert rows, "audit-36 must name the drifted repro s22/w1-repro-m5.py"
    row = "\n".join(rows)
    for token in ("assumptions moved", "repro_m5_failed_exit", "WIN when", "re-sealed"):
        assert token in row, f"DRIFT row missing {token!r}:\n{row}"
    mapping = (engine.status_exit_code("failed"), engine.status_exit_code("completed"))
    assert mapping == (1, 0), f"honest mapping absent on current main: {mapping}"
    proc = _s48w2_run_repro(tmp_path)
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"repro exited {proc.returncode}; tail:\n{combined[-1500:]}"
    signature = _s48w2_repro_signature(proc)
    assert signature == "" or signature.split("/")[0] == signature.split("/")[1], (
        f"repro signature not all-pass: {signature!r}"
    )
    assert signature, f"no all-pass GREEN signature in repro output:\n{combined[-1500:]}"
