# s30 w2 — spec-first pins for audit --corpus

You are w2 in season s30 (repo root: the parent of this .rumpun tree). Read
src/rumpun/audit.py, src/rumpun/cli.py (the audit verb), akar record
audit-18. You own tests/; w1 owns audit.py + cli.py. FILE TOOLS directly.
WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. audit --corpus invokes the runner as an isolated subprocess (stub
   runner script via monkeypatched path or a temp runner file) before
   ingesting; the fresh matrix's REGRESSION row arms the candidate.
2. A runner failing (exit 1) raises AuditError naming the runner and the
   exit code; no stale-matrix ingestion happens after the failure.
3. A runner timeout raises AuditError (bounded — the pin uses a short
   timeout on a sleeping stub; no wall-clock waits beyond it).
4. Without --corpus, audit output is byte-identical to the pre-s30
   audit (A/B pin; the s26 byte-identical pin keeps holding).
5. Regression: the 138-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (138 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns the implementations.

## Verify before finishing

Measured red set against current code in notes.md; the 138 existing
tests green.
