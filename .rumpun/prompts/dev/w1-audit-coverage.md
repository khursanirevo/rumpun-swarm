# s52 w1 — the audit coverage finding, landed at last

You are w1 in season s52 (repo root: the parent of this .rumpun tree).
Read src/rumpun/audit.py (run_audit, the corpus ingestion path),
tests/test_s43_w2_pins.py (the standing red contract), and akar records
audit-38 + s51-harvest. FILE TOOLS directly. WRITE ONLY inside your
workspace EXCEPT minimal documented audit.py changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. audit.py emits the s43 coverage finding when a corpus matrix is
   ingested: exactly one line of the spec shape
   "corpus coverage: N repro scripts PASS of M discovered (K SKIP)"
   covering every discovered script, not only the passing minority.
2. The finding obeys the s43 contract's honesty clauses: present at 0
   PASS (the honest floor), the gap arms zero candidates, "candidates:
   none" stays, and the record makes no "all green on main" claim while
   skips dominate. The three red pins in tests/test_s43_w2_pins.py are
   the contract; read them fully.
3. cli wiring unchanged; the emission rides the existing matrix
   ingestion path in run_audit.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns pins; the harness merges).
- Additive change: the suite floor holds, the s43 pins go green.

## Verify before finishing
Solo run: `.venv/bin/python -m pytest tests/test_s43_w2_pins.py -q` →
3 passed. Full suite: only the known race flakes may wobble. All in
notes.md.
