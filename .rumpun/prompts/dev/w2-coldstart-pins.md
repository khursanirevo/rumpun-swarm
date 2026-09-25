# s37 w2 — spec-first pins for the cold-start checker

You are w2 in season s37 (repo root: the parent of this .rumpun tree). Read
README.md (the quickstart), akar records audit-26 + usefulness-decade-3,
and s25's corpus-runner pins (the subprocess-tool pin pattern). You own
tests/; w1 owns tools/. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Spec-first pins (red against current code)

1. The checker exists and runs: a full run in a temp dir exits 0 with
   every step PASS in its output.
2. A broken step fails honestly: with a sabotaged init (read-only
   target), the checker exits nonzero naming the failed step.
3. Isolation: the checker leaves the REPO's own .rumpun untouched
   (byte-compare the repo ledger before/after).
4. Regression: the 175-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (175 tests kept).
- The pins run the checker via subprocess with the repo venv python;
  timeout bounded (120s), no wall-clock asserts beyond it.
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ or tools/ — w1 owns the checker.

## Verify before finishing

Measured red set against current code in notes.md; the 175 existing
tests green.
