# s31 w2 — spec-first pins for render-on-change

You are w2 in season s31 (repo root: the parent of this .rumpun tree). Read
src/rumpun/engine.py (state_hook + watcher), akar record audit-19. You own
tests/; w1 owns engine.py. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Spec-first pins (red against current code)

1. Change-gated: a slow stub whose state bytes never change renders
   exactly ONCE across 3+ watcher cycles (count hook invocations that
   pass the change gate — pin the gate, not wall-clock).
2. Byte change triggers re-render: rewrite state.json (same shape, new
   bytes) between cycles -> the hook fires again.
3. First cycle always renders (fresh watcher, never rendered).
4. Regression: the 142-test suite stays green (the 2 existing hook tests
   keep passing).

## Constraints

- tests additions-only vs the current repo file (142 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns engine.py.

## Verify before finishing

Measured red set against current code in notes.md; the 142 existing
tests green.
