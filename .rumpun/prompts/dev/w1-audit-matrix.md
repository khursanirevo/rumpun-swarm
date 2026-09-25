# s26 w1 — the audit ingests the corpus matrix

You are w1 in season s26 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/audit.py, tools/replay_corpus.py (the
runner whose output becomes audit input), and akar records audit-13 +
audit-14 (two consecutive zero-candidate audits: the blind spot is that
reflection never reads the one artifact that can show a main-line
regression). FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Deliverable: run_audit ingests the corpus matrix

Matrix source: the committed ledger copy at
.rumpun/akar/evidence/<latest-s>/replay-matrix.md (parse the table rows:
script | verdict | first failing line | note — a REGRESSION note or FAIL
verdict arms a candidate). Design decisions you own:
- Discovery: the newest replay-matrix.md across evidence dirs (or a
  runner-owned canonical path if cleaner — document the choice).
- A FAIL/REGRESSION row arms ONE candidate: "corpus regression: <script>
  <first-failing-line>; band: WIN when the named script passes on main",
  placed FIRST among candidates (a regression outranks improvements).
- An all-green matrix (>= 1 PASS row, zero FAIL) yields a plain finding:
  "corpus: N repro scripts green on main (no candidates)".
- A missing or unparseable matrix: no F-line, no candidate (backward
  compatible — audit-13/14 behavior preserved exactly).
- MAX_CANDIDATES still caps total; the regression candidate takes
  priority ahead of phase/route/calibration/stall triggers.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch collab.py, engine.py, evolve.py, cli.py, report.py,
  tests/ (w2 owns the pins; the harness merges).
- All existing audit pins (s13/s23 batches) stay green.

## Verify before finishing

Repros: fixture matrix with a REGRESSION row -> candidate cites it
first; all-green matrix -> finding only; absent matrix -> output
byte-identical to pre-s26 behavior (A/B compare); suite green against
patched copies. All in notes.md.
