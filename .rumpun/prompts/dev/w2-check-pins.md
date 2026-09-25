# s55 w2 — spec-first pins for the artifact check

You are w2 in season s55 (repo root: the parent of this .rumpun tree).
Read tools/replay_corpus.py (the isolated-runner precedent), ledger
records s54-harvest + audit-39, and the s52 pins (tests/test_s52_w2_pins.py)
as the shape precedent. You own tests/; w1 owns tools/ + cli. FILE TOOLS
directly. WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. `artifact_check s54 <close-commit>` (subprocess, 240s bound) exits 0
   on the honest close: the pins re-run green in the extracted tree, the
   digests recompute equal, and the record cites the exact commands run.
2. The checker detects the dishonest close: a ships row naming a file
   the tree lacks, or a digest that recomputes different, yields DELTA
   in the record and exit 1 (build a tampered fixture, never edit the
   real ledger).
3. Refusals are loud: a missing close commit, an unknown season id, or
   pins that fail to collect exit nonzero naming what is missing.

## Constraints
- tests/ additions-only; the checker runs via subprocess, bounded.
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ or tools/ - w1 owns them; the harness merges.

## Verify before finishing
Measured red set in notes.md; the honest-close pin green at merge; the
tampered-fixture pin green; the suite floor holds.
