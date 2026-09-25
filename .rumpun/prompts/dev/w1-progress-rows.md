# s24 w1 — content-based stall progress + harvest row fields

You are w1 in season s24 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/engine.py (the stall progress check
+ its M10 trade-off comment), src/rumpun/harvest.py, src/rumpun/cli.py
(the harvest verb), and akar records stall-rule-fired-on-runtime +
audit-12. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Fix 1 — content-based stall progress (the M10 candidate)

Today: progress = agent.log mtime (touching without writing defeats
detection). Fix: progress = the log's BYTE SIZE having grown (track the
last-seen size per live agent in the watcher's memory; a file whose size
is unchanged across cycles provides no progress regardless of mtime; a
grown file does). Keep the started_at floor for not-yet-created logs.
Update the M10 trade-off comment to describe the content-based rule.
Zero new polling; the size read rides the existing watcher cycle.

## Fix 2 — harvest rows carry band and observed again

Today: the harvest verb writes season rows with "band": "" and
"observed": "" (every row since s21) because the CLI grew no flags.
Fix: the harvest subcommand gains optional --band and --observed
arguments, passed through to harvest_season. The CLI docstring/help
names them. Empty defaults keep backward compatibility.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch lint.py, akar.py, evolve.py, collab.py, report.py,
  audit.py, tests/ (w2 owns the test pins; the harness merges).
- The 117-test suite stays green.

## Verify before finishing

Repros: (1) two stub agents past the same elapsed time — one touching
its log without appending (stays running until budget), one appending
bytes then going quiet (stalls) — fates differ; (2) harvest --band X
--observed Y writes the season row with both fields; without the flags,
both stay empty strings. Suite green against patched copies. In notes.md.
