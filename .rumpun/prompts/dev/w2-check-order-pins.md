# s59 w2 — spec-first pins for the close-check fallback

You are w2 in season s59 (repo root: the parent of .rumpun). Read
tools/artifact_check.py, src/rumpun/cli.py, and ledger records
s57-harvest + s58-harvest; the s58 pins (tests/test_s58_w2_pins.py) are
the shape precedent. You own tests/; w1 owns tools/. FILE TOOLS
directly. WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. The close case: a season whose DESIGN row exists only in the live
   worktree (uncommitted, the just-closed entry) checks through - the
   record lands with the live-row disclosure line, exit 0 (VERIFIED
   when everything else is green).
2. Tamper stays bound: a tampered extracted tree (a ghost ships file or
   a bad digest) still yields DELTA exit 1 even when the live-row
   fallback is in play.
3. Both sources present: the extracted row wins byte-for-byte; the
   record carries no live-row disclosure line.

## Constraints
- tests/ additions-only; subprocess pins, timeout bounded (240s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ or tools/ - w1 owns tools/; the harness merges.

## Verify before finishing
Measured red set in notes.md; all pins green at merge; the suite floor
holds.
