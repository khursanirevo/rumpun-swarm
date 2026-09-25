# s65 w1 — containment: a check delta gates the next start

You are w1 in season s65 (repo root: the parent of this .rumpun tree).
Read src/rumpun/engine.py (start_season's preflight), src/rumpun/cli.py
(cmd_check, cmd_harvest), and ledger records s64-harvest + check-s63 +
usefulness-decade-5 (the containment residual). FILE TOOLS directly.
WRITE ONLY inside your workspace EXCEPT minimal documented engine.py or
cli.py changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. season start reads the newest check-<sid> record for the campaign's
   previous closed season: a DELTA or structural refusal verdict blocks
   the start, naming the record; the block releases on a later VERIFIED
   check for that season or a ledger waiver record naming it.
2. The waiver is a ledger record (waiver:<sid> or the agreed shape):
   named in the block message, appendable only through the ledger
   discipline (sha-sealed), and the start gate accepts it as explicit
   operator release. Clean closes and VERIFIED checks start normally.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- Additive: the suite floor holds; the known race flakes stay the only reds.

## Verify before finishing
A fixture campaign with a DELTA record refuses; after a VERIFIED rerun
or a waiver record it starts. Suite floor. All in notes.md.
