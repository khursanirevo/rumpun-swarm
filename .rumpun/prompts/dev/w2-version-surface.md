# s82 w2 — fix the version-tracking surface (issue #8) + rerun the s79 panel (issue #9)

The panel found what the pins missed: installed_kancil_version reads
Python metadata in rumpun's environment, but kancil lives as an
isolated uv tool - a mismatch can yield alignment None and no card.

## Ground truth (measured 2026-09-17)
- issue #8 (OPEN): the panel's repro - a pack stamped 0.0.0 returned
  alignment None and no card while the CLI reports 2.2.5
- src/rumpun/skills.py:83: installed_kancil_version uses
  importlib.metadata.version("kancil")
- the panel route (gpt-6-astra, bounded 300s) is proven; s79's only
  record is panel-s79-error (a codex MCP transport crash, infra)

## Task
1. Fix the surface (issue #8's required correction): read the ROUTE
   executable's version, not Python metadata - `kancil --version`-equivalent
   via the resolved binary (subprocess, bounded, offline-pinnable with
   an injected runner); fall back to importlib.metadata only when the
   binary is absent. The alignment matrix keeps its three states.
2. Pins (tests/test_s82_w2_pins.py, _s82w2_ prefix, offline): the
   injected-runner contract (the binary's output parsed, garbage ->
   None), the fallback ordering, the 0.0.0-stamp repro from issue #8
   now rendering the card.
3. Rerun the s79 panel ONCE: `rumpun audit --panel s79` - a verdict or
   an honest error record seals; issue #9 gets the outcome commented
   (one live call, disclosed in notes).
4. notes.md REQUIRED: the surface fix, the pin map, the s79 outcome.

## Bounds
- Edits: src/rumpun/skills.py, src/rumpun/kanban.py if the card needs
  the new signal, tests/. notes.md REQUIRED. One panel call, no
  retries. No .rumpun state edits.
