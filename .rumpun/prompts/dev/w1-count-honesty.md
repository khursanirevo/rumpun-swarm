# s64 w1 — the counts read the whole ledger

You are w1 in season s64 (repo root: the parent of this .rumpun tree).
Read tools/usefulness_audit.py (the composer), src/rumpun/audit.py (the
F3/F5 verdict surfaces), and ledger records usefulness-decade-5 + audit-41
(the residual this lands). FILE TOOLS directly. WRITE ONLY inside your
workspace EXCEPT minimal documented tools/ changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. The composer counts the whole ledger: every season yaml under
   .rumpun/seasons/ contributes exactly one count slot - WIN, LOSS,
   NEUTRAL, INVALID, or MISSING (no verdict row and not running).
2. The salvaged split propagates: the counts carry the s62 salvage
   marks (X WIN, of which Y salvaged) wherever the totals render - the
   composer's summary and the verdict history surface alike.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- Additive: the suite floor holds; the known race flakes stay the only reds.

## Verify before finishing
A composer run over the real ledger counts 60+ season slots with the
missing ones named. Suite floor. All in notes.md.
