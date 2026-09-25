# s66 w1 — the operator surface: kanban verb + adhd preinstall

You are w1 in season s66 (repo root: the parent of this .rumpun tree).
Read src/rumpun/cli.py (the verb wiring precedent), src/rumpun/audit.py
(armed candidates), src/rumpun/harvest.py (salvage marks), and ledger
records s65-harvest + audit-42 + directives seq 7/8/10. FILE TOOLS
directly. WRITE ONLY inside your workspace EXCEPT minimal documented
cli.py + scaffold changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. `rumpun kanban` renders four columns from existing state, no new
   state file: BACKLOG (armed audit candidates, drafted-only season
   seeds), DOING (the running season from runs state), NEED HUMAN (the
   unset campaign_cost_cap, any containment blocks, stale directive
   statuses), DONE (harvested seasons, verdict + salvaged marks).
2. `rumpun init` preinstalls the adhd output rules: init copies the
   rules card into the campaign (the INSTALL.md source is
   github.com/ayghri/i-have-adhd; the rules ship verbatim, not
   paraphrased) and prints the activation line.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- Additive: the suite floor holds; the known race flakes stay the only reds.

## Verify before finishing
`rumpun kanban` on this campaign renders all four columns with real
entries; a fresh init installs the rules card. notes.md.
