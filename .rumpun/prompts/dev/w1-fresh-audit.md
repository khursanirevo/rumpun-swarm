# s30 w1 — audit --corpus: fresh matrix before ingestion

You are w1 in season s30 (repo root: the parent of this .rumpun tree). Read
src/rumpun/audit.py (the s26 matrix ingestion), src/rumpun/cli.py (the
audit verb), tools/replay_corpus.py (the runner: its matrix write path and
exit contract), and akar record audit-18. FILE TOOLS directly. WRITE ONLY
inside your workspace. 40 minutes.

## Deliverable: --corpus flag on the audit verb

- cli: `rumpun audit [--last N] [--corpus]` — the flag routes to a fresh
  corpus run before ingestion.
- audit.py: a `refresh_corpus_matrix(root, runner_path, timeout_s=120)`
  that runs tools/replay_corpus.py as an isolated subprocess (repo venv
  python, timeout, captured output), then run_audit ingests the matrix
  the runner just wrote.
- Honesty: a runner nonzero exit or timeout raises AuditError naming the
  runner and the exit code (the audit must NOT silently ingest a stale
  or partial matrix). The runner's own output is never echoed into the
  audit record (only the verdict counts land there).
- Default behavior without --corpus is byte-identical (the s26 pins hold).
- Runner path: tools/replay_corpus.py resolved relative to the repo root;
  a missing runner with --corpus is an AuditError.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tools/replay_corpus.py's verdict logic, collab.py,
  engine.py, harvest.py, evolve.py, report.py, tests/ (w2 owns the pins).
- The 138-test suite stays green.

## Verify before finishing

Repros: audit --corpus on a fixture root with a stub runner (echoes a
matrix with a REGRESSION row) arms the candidate from the FRESH matrix;
a stub runner exiting 1 raises AuditError with the code; no --corpus is
byte-identical (A/B). Suite green against patched copies. All in notes.md.
