# s63 w1 — the ships classifier learns runtime artifacts

You are w1 in season s63 (repo root: the parent of this .rumpun tree).
Read tools/artifact_check.py (the ships-diff clause judge, the s61 DELTA
case), .rumpun/ledger/2026-09-16_check-s61.md (the diagnosed false
positive), and ledger records s62-harvest + check-s61. FILE TOOLS
directly. WRITE ONLY inside your workspace EXCEPT minimal documented
tools/artifact_check.py changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. The clause judge distinguishes file-shaped tokens: a token framed as
   run-time output ("writes <artifact>", close-time, runs/<sid>) checks
   the campaign's runs state (the live runs/<sid>/ holds it) and records
   the classification in the clause evidence; committed-tree claims bind
   exactly as before.
2. A genuinely missing committed file still yields DELTA exit 1: the
   distinction covers run-time framing only, never a bailout.
3. The clause evidence names the classification per file-shaped token
   (runtime-checked against runs/<sid>/ vs committed-tree claim).

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- Additive: the suite floor holds; the known race flakes stay the only reds.

## Verify before finishing
A checker run over a fixture close whose live runs dir holds the
artifact checks through with the classification recorded; a ghost
committed-file claim still DELTAs. notes.md.
