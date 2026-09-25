# s27 w2 — spec-first pins for tools/render_dashboard.py

You are w2 in season s27 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/report.py, akar record audit-15. You
own tests/; w1 owns the tool. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Spec-first pins (red against current code - the tool does not exist)

1. A fixture root with two stateful seasons + one stateless dir renders
   exactly 2 season reports + index + discoveries index; the stateless
   season logs exactly one skip reason.
2. Determinism: two consecutive runs of the tool over unchanged bytes
   produce byte-identical outputs (hash compare).
3. The tool imports engine.state_path for the state rule (source-level
   pin via inspect.getsource containing "state_path").
4. Total-failure exit: a root with no .rumpun tree exits nonzero.
5. Regression: the 129-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (129 tests kept).
- The pins run the tool via subprocess (its __main__ entry) with the
  repo .venv python; no wall-clock asserts.
- logging, never print; ruff clean (line-length 100); py3.10+.

## Verify before finishing

Measured red set against current code in notes.md; the 129 existing
tests green.
