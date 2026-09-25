# s56 w2 — spec-first pins for the check verb

You are w2 in season s56 (repo root: the parent of this .rumpun tree).
Read tools/artifact_check.py (the landed checker), src/rumpun/cli.py, and
ledger records s55's harvest + audit-39; the s55 pins
(tests/test_s55_w2_pins.py) are the shape precedent. You own tests/;
w1 owns cli.py + audit.py. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Spec-first pins (red against current code)

1. `rumpun check s54 <close-commit>` (subprocess, 240s bound) exits 0
   and writes the check-s54 ledger record carrying VERIFIED - the same
   verdict the direct tool run produces.
2. The audit F1 comment names the runs path: no "rimba" survives in
   src/rumpun/audit.py's user-visible comments (the grep pin over the
   source file, the s54 rename sweep's shape).
3. A bad season id or unresolvable commit refuses nonzero through the
   verb, naming what is missing (the checker's own refusal contract).

## Constraints
- tests/ additions-only; the verb pins subprocess, timeout bounded (240s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ or tools/ - w1 owns them; the harness merges.

## Verify before finishing
Measured red set in notes.md; the verb pins green at merge; the two known
race flakes stay the only reds.
