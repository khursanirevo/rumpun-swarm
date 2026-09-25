# s62 w1 — a salvaged win reads as salvaged

You are w1 in season s62 (repo root: the parent of this .rumpun tree).
Read src/rumpun/cli.py (cmd_harvest), src/rumpun/harvest.py (the harvest
writer), src/rumpun/audit.py (the F3 verdict histogram), and ledger
records s59-harvest + usefulness-decade-5 (the criticism this lands).
FILE TOOLS directly. WRITE ONLY inside your workspace EXCEPT minimal
documented cli.py/harvest.py/audit.py changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. cmd_harvest reads the season's terminal state (runs/<sid>/
   _season/state.json: stopped_stall vs completed) before writing: a
   salvaged season's verdict row gains a "salvaged": true field and the
   harvest record's title carries "(salvaged)".
2. The audit's F3 verdict histogram splits the aggregate: "X WIN (Y
   salvaged), Z LOSS, W INVALID" - and the usefulness brief's counts can
   do the same. No existing record is rewritten; the split reads the
   rows as they are.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- Additive: the suite floor holds; the known race flakes stay the only reds.

## Verify before finishing
A stopped_stall fixture harvests marked; a completed fixture unmarked;
the histogram splits. Suite floor. All in notes.md.
