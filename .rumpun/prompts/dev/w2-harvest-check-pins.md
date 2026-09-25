# s57 w2 — spec-first pins for the harvest-integrated check

You are w2 in season s57 (repo root: the parent of this .rumpun tree).
Read src/rumpun/cli.py (cmd_harvest), tools/artifact_check.py, and ledger
records s56-harvest + audit-39/40; the s56 pins
(tests/test_s56_w2_pins.py) are the shape precedent. You own tests/;
w1 owns cli.py. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Spec-first pins (red against current code)

1. `rumpun harvest <sid> ...` on a fixture season lands BOTH the verdict
   row and the check-<sid> record in the ledger dir (subprocess, 240s
   bound; the fixture season's ships must be check-compatible).
2. The honesty path: a tampered fixture whose check yields DELTA still
   lands the verdict row, the check-<sid> record carries DELTA beside
   it, and nothing rewrites the verdict (subprocess, bounded).
3. The check's structural refusal (unknown sid) exits nonzero and names
   what is missing; the harvest record of the honest fixture is
   byte-stable across two runs.

## Constraints
- tests/ additions-only; subprocess pins, timeout bounded (240s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ - w1 owns cli.py; the harness merges.

## Verify before finishing
Measured red set in notes.md; both pins green at merge; the suite floor
holds.
