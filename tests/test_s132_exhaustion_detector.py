"""s132 w1 pins -- the plan names candidate exhaustion when the audits repeat.

Spec source: the s132 w1 brief (.rumpun/runs/s132/w1/prompt.md) and the
seam contract in src/rumpun/evolve.py (draft_next, the verb behind
`rumpun evolve plan`). audit-48 named three candidates and every one is a
standing decade residual an earlier audit already named: the audit
pipeline has stopped finding anything new, which is the stopping-rule
moment the directive frame defines. The rule this season lands: when the
most recent audit record's candidates ALL match candidates named in any
earlier audit record (the repetition test), the plan output surfaces
"the candidate pool is repeating: the operator decides" with the repeated
count; any fresh candidate keeps the announcement silent. The hint never
blocks the draft, and the drought hint family (s116) is untouched.

Offline: in-process over tmp_path fixture campaigns; audit records land
only in the tmp ledger through akar.append_record -- the real campaign
ledger is never written, and no season runs.

Grafting: drop this file into tests/. Helpers and constants carry the
_s132 prefix; nothing collides with existing defs.

Red-first honesty: the announcing pins ran red before the implementation
landed: pin1 and pin5 failed on the missing phrase (2 failed, 3 passed,
observed on the shared tree before the evolve.py edit). The silence pins
(pin2/pin3/pin4) are green on arrival: nothing announced on the
unmodified tree either. After the implementation, all five pass.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from rumpun import akar, evolve

# The three audit-48 candidate bodies, verbatim from the real ledger
# (2026-09-20_audit-48.md), each a standing usefulness-decade-1 residual.
_S132_A = (
    "usefulness residual: s30 and s32 count post-stop integration as WIN. "
    "Earlier salvaged seasons retain LOSS, making aggregate outcomes "
    "inconsistent. (usefulness-decade-1)"
)
_S132_B = (
    "usefulness residual: The campaign supplies no total cost accounting. "
    "The last explicit cost-cap status remains unset despite a declared "
    "budget invariant. (usefulness-decade-1)"
)
_S132_FRESH = (
    "usefulness residual: a candidate no earlier audit has ever named "
    "(usefulness-decade-1)"
)
_S132_PHRASE = "the candidate pool is repeating: the operator decides"


def _s132_season_text(sid: str, parent_id: str | None) -> str:
    """One draftable lineage season: id, optional parent, methodology.pipeline."""
    lines = [
        f"id: {sid}",
        f'goal: "fixture {sid}"',
        "metric: m",
        "mode: fight",
        "methodology:",
        '  approach: "x"',
        "  evidence: []",
        "  primary_change:",
        "    type: add",
        "    node: execute",
        '    baseline: "b"',
        '    expected_band: "WIN if x"',
        '    rollback: "git revert"',
        f'    eval_window: "{sid}"',
        "  pipeline:",
        "    - phase: execute",
        "      primitive: execute",
        "      agents: writers",
        "      prompt: prompts/dev/dummy.md",
        "      writes: results.jsonl",
    ]
    if parent_id is not None:
        lines.insert(1, f"parent: {parent_id}")
    return "\n".join(lines) + "\n"


def _s132_campaign(tmp_path: Path) -> Path:
    """A tmp campaign with one lineage season s1 and no parent.

    The drought walks one close (1 < 6), so the s116 assessment hint stays
    silent and the log carries only what these pins test. root is the
    state dir draft_next resolves through paths.seasons_dir (the engine
    convention). The real campaign ledger is never touched.
    """
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    season = root / "seasons" / "s1.yaml"
    season.write_text(_s132_season_text("s1", None), encoding="utf-8")
    return root


def _s132_audit(
    root: Path, n: int, bodies: list[str], extra_body: str | None = None
) -> Path:
    """audit-<n> into the tmp campaign ledger; one candidate: line per body."""
    lines = [f"candidate: {body}" for body in bodies]
    if extra_body is not None:
        lines.append(extra_body)
    return akar.append_record(
        root, f"audit-{n}", "reflection audit", "\n".join(lines)
    )


def _s132_plan(caplog: pytest.LogCaptureFixture, root: Path) -> str:
    """Plan s2 from s1; the draft must land (the hint never blocks); the log."""
    with caplog.at_level(logging.DEBUG, logger="rumpun.evolve"):
        drafted = evolve.draft_next(root, root / "seasons" / "s1.yaml")
    assert drafted.is_file(), f"the plan never produced the draft: {drafted}"
    return caplog.text


def test_s132_pin1_repeating_pool_announces_with_count(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Every latest-audit candidate repeats an earlier one: announce 2 of 2.

    audit-1 names A and B; audit-2 names the same A and B. The repetition
    test holds, so the plan output carries the phrase, names audit-2, and
    carries the count, and the draft still lands.
    """
    root = _s132_campaign(tmp_path)
    _s132_audit(root, 1, [_S132_A, _S132_B])
    _s132_audit(root, 2, [_S132_A, _S132_B])
    log = _s132_plan(caplog, root)
    assert _S132_PHRASE in log
    assert "(audit-2, 2 of 2 candidates repeat earlier audits)" in log


def test_s132_pin2_fresh_candidate_stays_silent(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """One fresh candidate in the newest audit keeps the announcement off."""
    root = _s132_campaign(tmp_path)
    _s132_audit(root, 1, [_S132_A, _S132_B])
    _s132_audit(root, 2, [_S132_A, _S132_FRESH])
    log = _s132_plan(caplog, root)
    assert _S132_PHRASE not in log


def test_s132_pin3_single_audit_stays_silent(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """One audit record alone has no earlier pool; nothing can repeat."""
    root = _s132_campaign(tmp_path)
    _s132_audit(root, 1, [_S132_A, _S132_B])
    log = _s132_plan(caplog, root)
    assert _S132_PHRASE not in log


def test_s132_pin4_zero_candidates_stays_silent(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A newest audit naming zero candidates stays silent.

    The repetition test is over the candidates the newest audit names;
    with none named, nothing repeats and a "0 of 0" announcement would
    fake a signal the audits did not give.
    """
    root = _s132_campaign(tmp_path)
    _s132_audit(root, 1, [_S132_A])
    _s132_audit(
        root, 2, [], extra_body="corpus: green on main (no candidates)"
    )
    log = _s132_plan(caplog, root)
    assert _S132_PHRASE not in log


def test_s132_pin5_pool_unions_all_earlier_audits(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The pool is every candidate from every earlier audit, not the last one.

    audit-1 names A, audit-2 names B, audit-3 names A and B: each newest
    candidate repeats a different earlier audit, so the test holds with
    the 2-of-2 count naming audit-3.
    """
    root = _s132_campaign(tmp_path)
    _s132_audit(root, 1, [_S132_A])
    _s132_audit(root, 2, [_S132_B])
    _s132_audit(root, 3, [_S132_A, _S132_B])
    log = _s132_plan(caplog, root)
    assert _S132_PHRASE in log
    assert "(audit-3, 2 of 2 candidates repeat earlier audits)" in log
