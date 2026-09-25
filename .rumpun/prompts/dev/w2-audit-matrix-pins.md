# s26 w2 — spec-first pins for the matrix-ingesting audit

You are w2 in season s23's successor s26 (repo root: the parent of this
.rumpun tree). Read DESIGN.md sections 13-15, src/rumpun/audit.py, akar
records audit-13 + audit-14. You own tests/; w1 owns audit.py. FILE TOOLS
directly. WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. Matrix ingestion: run_audit reads the newest replay-matrix.md under
   akar evidence; a REGRESSION/FAIL row arms a candidate placed first,
   citing the script and first failing line; the cap still applies.
2. All-green matrix: a plain "corpus: N repro scripts green" finding,
   never a candidate.
3. Backward compatibility: with no matrix present, run_audit's output is
   byte-identical to the pre-s26 audit (A/B pin).
4. Malformed matrix rows are skipped from ingestion (one DEBUG each),
   never crash the audit.
5. Regression: the 124-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (124 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns audit.py.

## Verify before finishing

Measured red set against current code in notes.md; the 124 existing
tests green; fixture matrices minimal and readable.
