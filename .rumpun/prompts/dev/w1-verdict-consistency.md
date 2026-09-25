# s35 w1 — verdict-versus-artifact cross-check in run_audit

You are w1 in season s35 (repo root: the parent of this .rumpun tree). Read
src/rumpun/audit.py (run_audit + the F3/F5 blocks + candidate arming), and
akar records audit-24 + usefulness-decade-3. FILE TOOLS directly. WRITE
ONLY inside your workspace. 40 minutes.

## Deliverable: the verdict-consistency cross-check

For each audited engine season holding BOTH a season verdict (the last
season-level verdicts.jsonl row) and results.jsonl rows with "verdict"
fields: any unit row verdict FAIL under a season verdict WIN arms ONE
candidate: "candidate: verdict mismatch: <sid> harvested WIN while its
results carry FAIL (<unit>); band: WIN when the verdict matches the
artifacts". The candidate joins the existing proposals before the cap.
Consistent seasons arm nothing; seasons without results rows are
unaffected; the F3 histogram is unchanged. Existing pins stay green.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch collab.py, engine.py, harvest.py, evolve.py, lint.py,
  cli.py, report.py, tools/, tests/ (w2 owns the pins; the harness merges).
- The 166-test suite stays green.

## Verify before finishing

Repros: a fixture WIN season with a FAIL unit row arms the candidate
naming both; a consistent fixture arms nothing; a season with no results
rows is unaffected. Suite green against patched copies. All in notes.md.
