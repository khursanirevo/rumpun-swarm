# s31 w1 — render-on-change for the watcher's state hook

You are w1 in season s31 (repo root: the parent of this .rumpun tree). Read
src/rumpun/engine.py (state_hook + the watcher cycle) and akar record
audit-19. Evidence: the s30 launch rendered the index once per watcher
cycle — ~1600 identical renders for one season. FILE TOOLS directly.
WRITE ONLY inside your workspace. 40 minutes.

## Deliverable: change-gated rendering

In the watcher (start_season's loop), before calling state_hook: hash the
persisted state.json bytes (hashlib.sha256, read once); render only when
the hash differs from the previous cycle's (module-level or closure-held
per-season cache — the watcher is single-season scoped, closure is fine).
First cycle always renders. Downgrade the hook's own render log: the
per-render INFO already comes from report functions; the hook adds
nothing. The cli's finally-block terminal render stays unconditional.
Zero new polling: the hash read rides the existing cycle.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch collab.py, harvest.py, evolve.py, lint.py, akar.py,
  report.py, tools/, tests/ (w2 owns the pins; the harness merges).
- The 142-test suite stays green; the hook tests (2) must keep passing
  (the first render still fires on cycle 1).

## Verify before finishing

Repro: a stub season whose state bytes change mid-run renders >= 2 times;
a stub whose bytes never change renders exactly once across 3+ cycles
(count via a counting hook wrapper or caplog on the render logger).
Suite green against patched copies. Both in notes.md.
