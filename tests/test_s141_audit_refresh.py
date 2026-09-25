"""s141 w2: the audit refresh feeds the detector.

Ground truth measured 2026-09-21 (repo HEAD 12827ad, /tmp/s141-w2-audit.out):

- `rumpun audit --last 5` ran fresh and appended ledger record audit-49
  (.rumpun/ledger/2026-09-21_audit-49.md) -- the audit verb's designed
  write at measurement time; this file reads only.
- audit-49's three candidate lines are byte-identical to audit-48's
  (diff clean): the standing usefulness-decade-1 residuals. No fresh
  class was named.
- evolve._candidate_exhaustion reads that same ledger and announces the
  repetition: audit-49, 3 of 3 candidates repeat earlier audits.

The record: the newest audit id at the refresh, its candidates, the
comparison verdict against audit-48. A red on the newest-id pin means a
newer audit landed since this refresh; the next steady-state cycle
re-runs the audit and refreshes the record.
"""

from __future__ import annotations

import re
from pathlib import Path

from rumpun import evolve

REFRESH_DATE = "2026-09-21"
NEWEST_AUDIT = "audit-49"
AUDIT48_DATE = "2026-09-20"
PREVIOUS_AUDIT = "audit-48"

# The three candidate lines, verbatim from both records (diff-clean).
_AUD48_L1 = (
    "candidate: usefulness residual: s30 and s32 count post-stop "
    "integration as WIN. Earlier salvaged seasons retain LOSS, making "
    "aggregate outcomes inconsistent. (usefulness-decade-1)"
)
_AUD48_L2 = (
    "candidate: usefulness residual: The campaign supplies no total cost "
    "accounting. The last explicit cost-cap status remains unset despite "
    "a declared budget invariant. (usefulness-decade-1)"
)
_AUD48_L3 = (
    "candidate: usefulness residual: Automatic continuation lacks a "
    "demonstrated usefulness threshold or stopping rule after actionable "
    "candidates disappear. (usefulness-decade-1)"
)
AUDIT48_CANDIDATES = [_AUD48_L1, _AUD48_L2, _AUD48_L3]
AUDIT49_CANDIDATES = [_AUD48_L1, _AUD48_L2, _AUD48_L3]

VERDICT = "repetition"
EXPECTED_HINT = (
    "the candidate pool is repeating: the operator decides "
    f"({NEWEST_AUDIT}, 3 of 3 candidates repeat earlier audits)"
)

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / ".rumpun" / "ledger"
_AUDIT_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})_audit-(\d+)\.md$")


def _candidate_lines(path: Path) -> list[str]:
    """The record's candidate lines in file order."""
    return [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("candidate: ")
    ]


def _newest_audit_file() -> Path:
    """The audit record highest by (ledger date, id), the detector's order."""
    audits = []
    for entry in LEDGER.iterdir():
        if match := _AUDIT_FILE.match(entry.name):
            audits.append((match.group(1), int(match.group(2)), entry))
    assert audits, f"no audit records under {LEDGER}"
    return max(audits, key=lambda item: (item[0], item[1]))[2]


def test_newest_audit_is_the_refreshed_record() -> None:
    """The ledger's newest audit (date, id) is still the refreshed one."""
    newest = _newest_audit_file()
    assert newest.name == f"{REFRESH_DATE}_{NEWEST_AUDIT}.md", (
        f"a newer audit landed since the {REFRESH_DATE} refresh: {newest.name}"
    )


def test_audit49_candidates_match_the_record() -> None:
    """audit-49 still reads the three recorded candidate lines, verbatim."""
    recorded = _candidate_lines(LEDGER / f"{REFRESH_DATE}_{NEWEST_AUDIT}.md")
    assert recorded == AUDIT49_CANDIDATES


def test_candidates_repeat_audit48() -> None:
    """The refresh repeats audit-48's candidates; no fresh class named."""
    audit48 = _candidate_lines(LEDGER / f"{AUDIT48_DATE}_{PREVIOUS_AUDIT}.md")
    assert audit48 == AUDIT48_CANDIDATES
    assert audit48 == _candidate_lines(
        LEDGER / f"{REFRESH_DATE}_{NEWEST_AUDIT}.md"
    )
    assert VERDICT == "repetition"


def test_detector_announces_the_repetition() -> None:
    """The live detector fires on the real ledger, matching the verdict."""
    hint = evolve._candidate_exhaustion(REPO / ".rumpun")
    assert hint == EXPECTED_HINT
    assert (hint is not None) == (VERDICT == "repetition")
