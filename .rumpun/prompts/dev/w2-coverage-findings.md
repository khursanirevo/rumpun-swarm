# s43 w2 — the corpus coverage finding + spec-first pins

You are w2 in season s43 (repo root: the parent of this .rumpun tree). Read
src/rumpun/audit.py (the s26 corpus ingestion + candidate arming), akar
records audit-32 + usefulness-decade-4 (residual 10: six repro scripts do
not prove 53 ratified behaviors). You own tests/; w1 owns lint.py +
audit.py. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Deliverable: the corpus coverage finding (audit.py is w1's file —
coordinate: w1 lands it in audit.py alongside the DRIFT arming; your
deliverable is the spec + the pins)

The audit carries a standing coverage finding when a fresh matrix exists:
"corpus coverage: N repro scripts PASS of M discovered (K SKIP); coverage
gap is recorded, not hidden" — derived from the matrix's own rows
(PASS/FAIL/REGRESSION vs SKIP counts). Never a candidate by itself; the
number is honest however low.

## Spec-first pins (red against current code)

1. Coverage finding: a fixture matrix (6 PASS, 47 SKIP) yields the
   coverage finding with both numbers.
2. The finding is a finding, never a candidate.
3. Mismatch arming (w1's): a DRIFT row arms a candidate citing the
   drifted script; FAIL/REGRESSION keep priority.
4. Falsify reachability (w1's lint): an unreachable-reader season errors
   naming the unreachable artifact; a reachable one passes.
5. Regression: the 171-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (171 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns lint.py + audit.py.

## Verify before finishing

Measured red set against current code in notes.md; the 171 existing
tests green.
