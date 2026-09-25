# s59 w1 — the close check reads the fresh row

You are w1 in season s59 (repo root: the parent of this .rumpun tree).
Read tools/artifact_check.py (ships_row, the ingestion order),
src/rumpun/cli.py (_run_check, cmd_harvest), and ledger records
s57-harvest + s58-harvest (the wrinkle's live fire). FILE TOOLS
directly. WRITE ONLY inside your workspace EXCEPT minimal documented
tools/artifact_check.py changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. ships_row gains the close-time fallback: when the extracted
   DESIGN.md has no row for <sid> but the LIVE worktree DESIGN.md has
   one, the checker uses the live row and records the fact - a line in
   the check record: "ships row read from the live worktree (the
   close's own entry postdates the commit)".
2. Tamper detection binds to the extracted tree exactly as before: the
   fallback covers ONLY the missing fresh ships row; a tampered file,
   digest, or seal still yields DELTA with exit 1.
3. Both sources present: the extracted row wins; the fallback never
   fires and no disclosure line appears.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- Additive: the suite floor holds; the known race flakes stay the only reds.

## Verify before finishing
Check s58 @ 1737437... wait - check the CURRENT close case: after this
season's merge, the next close's harvest runs the checker; until then,
simulate with a repo whose DESIGN.md carries the fresh row uncommitted.
notes.md.
