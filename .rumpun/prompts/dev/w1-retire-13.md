# s87 w1 — retire issue #13 on the landed evidence; audit the board

Issue #13 (the panel's suite gate cell-scoping) was fixed in s86 with
pins and dry-runs. Your lane: retire it properly, then take the
board's honest inventory.

## Ground truth (measured 2026-09-17)
- issue #13 (OPEN): fixed in s86 - the suite-claim scan spans the
  whole ships row; the real s80/s81/s82 rows verified via dry-runs
  (two pass, one refuses correctly); 10 pins across two files
- the board: #5 OPEN by design (the repro-backed standard), #11/#12
  OPEN (the route credits, operator-side), everything else closed

## Task
1. Retire #13: comment it with the s86 evidence (the row-wide scan,
   the red-before dry-runs, the 10 pins) citing the sealed s86-harvest
   record, then close it.
2. The board inventory: list every open issue with its honest state
   (#5 the standing standard; #11/#12 the credits). Record the table
   in notes.md — what remains, what each waits on.
3. notes.md REQUIRED: the retirement evidence, the inventory table.

## Bounds
- One live comment+close pair for #13. Read-only otherwise. notes.md
  REQUIRED.
