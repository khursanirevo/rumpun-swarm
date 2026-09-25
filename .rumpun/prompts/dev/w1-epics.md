# s58 w1 — epics as data: the declaration and the rollup verb

You are w1 in season s58 (repo root: the parent of this .rumpun tree).
Read src/rumpun/cli.py (the verb wiring precedent), src/rumpun/lint.py
(the preflight patterns), src/rumpun/engine.py (read_status, runs state),
and ledger records s56-harvest + audit-40 + the directive (ledger
directives seq 5). FILE TOOLS directly. WRITE ONLY inside your workspace
EXCEPT minimal documented cli.py + lint.py changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. The epic declaration: .rumpun/epics.yaml (campaign-level; created by
   `rumpun epics --init`): mapping epic id -> {title, goal, seasons:
   [...]}. Lint rules: epic ids ^[a-z0-9][a-z0-9_-]*$, member seasons
   exist as yaml ids, no member in two epics.
2. The verb: `rumpun epics [--init]` renders one line per epic - id, the
   season span, the verdict rollup (X WIN / Y LOSS / Z other, derived
   from runs state and harvest verdicts), the title - and honestly marks
   a member with no run state. Missing epics.yaml prints a flat hint,
   not an error. --init scaffolds the file from the season yamls.
3. DESIGN section 16 gains a short epics-format note (prose, three lines).

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- The ledger is never written by this feature (append-only preserved).
- Additive: the suite floor holds; the known race flakes stay the only reds.

## Verify before finishing
epics.yaml with two epics over real seasons renders the rollup; a
duplicate member lints out. Suite floor. All in notes.md.
