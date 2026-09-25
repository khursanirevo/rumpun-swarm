# s19 w2 — H7 citation digest enforcement + pins for H2/H3/H7

You are w2 in season s19 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/lint.py (the _citation_resolves
function), src/rumpun/akar.py, akar record codex-review-2026-09-14 (H7 and
the H2/H3 reproductions), and s18's evidence (how repro-first work is
structured: .rumpun/akar/evidence/s18/). You own lint.py; w1 owns
engine.py. FILE TOOLS directly. 40 minutes.

## H7 — citation resolution must compare the digest

Today: _citation_resolves matches the akar:id@digest syntax and checks the
record file contains the id, but NEVER compares the sha256 digest against
the record's recorded sha256 line — altered evidence passes the evolution
gate (reviewer reproduced: wrong hash and partial id both accepted).
Fix in lint.py: resolve the exact record (filename akar/<date>_<id>.md via
the same scan akar uses), recompute the body digest the way akar records
it, and compare the cited digest (full value or unique prefix of >= 8 hex
chars). Mismatch -> citation does NOT resolve (error names the citation).
Existing seasons' citations (all real records) must still resolve.

## Spec-first tests (pin H2, H3, H7)

- H7: a valid citation resolves; a tampered digest fails with a naming
  error; a tampered RECORD body fails against the original citation;
  an >= 8-char prefix resolves.
- H2 (against w1's patch): a mismatched proc_start is not signaled and
  logs the warning; a matching one signals (assert via a stub process
  writing a marker file, no wall-clock dependence).
- H3 (against w1's patch): a pwd route records the workspace path as cwd.

## Constraints

- tests additions-only vs the current repo file (84 tests kept).
- lint.py patch as a workspace copy + notes.md anchors (harness merges).
- logging, never print; ruff clean (line-length 100); py3.10+.

## Verify before finishing

Measured red set against current code in notes.md; 84 existing tests
green; your lint.py copy passing your H7 tests in a scratch tree.
