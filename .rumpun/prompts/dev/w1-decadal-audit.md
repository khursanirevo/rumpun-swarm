# s33 w1 — the decadal usefulness audit (tools + audit trigger)

You are w1 in season s33 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-16, src/rumpun/audit.py (run_audit + candidate
arming), src/rumpun/cli.py (verb wiring), tools/replay_corpus.py (the
subprocess-runner pattern), and akar records codex-usefulness-2026-09-15 +
audit-19. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Deliverable 1: tools/usefulness_audit.py

Composes the auditor brief from the ledger (season count from musim/,
verdict history from rimba/*/verdicts.jsonl season rows, the DESIGN
sections-13-16 text), writes it to a temp prompt file, invokes the
different-model route from rumpun.yaml (config key usefulness.route,
default gpt-6-astra's codex bypass command) with stdin closed, captures
the output, extracts the final verdict line (USEFUL / PARTIALLY USEFUL /
SELF-LOOP DOING NOTHING), and appends an akar record
"usefulness-decade-<N>" carrying the verdict, the residuals the auditor
listed, and a pointer to the captured output under evidence.
Isolation: subprocess, own process group, hard timeout (300s), stdin
from /dev/null, captured streams never echoed into the record. Refuses
honestly (nonzero) if the route is missing, the call fails, or no
verdict line parses.

## Deliverable 2: the audit decade trigger

run_audit gains a finding: when the season count crosses a multiple of
10 (floor(count/10) > the number of usefulness-decade-* records), a
finding "usefulness audit due for decade N (different-model review)"
fires. Never a candidate by itself - the verdict record's residuals arm
candidates through the existing matrix/candidate machinery. audit-19/20
behavior otherwise unchanged (backward compatible).

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Never echo prompt content or route output into the record beyond the
  verdict line and residual summaries.
- Do not touch collab.py, engine.py, harvest.py, evolve.py, report.py,
  tests/ (w2 owns the pins; the harness merges).

## Verify before finishing

Repros: the decade finding fires on a 10-season fixture ledger and not
on 9; the runner against a stub route command writes the akar record
with a parsed verdict; a failing route raises honestly. Suite green
against patched copies. All in notes.md.
