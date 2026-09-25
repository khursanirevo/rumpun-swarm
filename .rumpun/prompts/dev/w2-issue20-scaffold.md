# s102 w2 — issue #20: the scaffold ships the checker

The khursani campaign (v0.11.0) scaffolded without
tools/artifact_check.py; every harvest errored checker-not-found; the
workaround was a manual copy from the source repo. Reproduce on
CURRENT main first: fixed → close with evidence; still broken → fix.

## Ground truth (measured 2026-09-18)
- issue #20 (OPEN): the issue's own error log is the spec — harvest
  logs `ERROR checker not found: <repo>/tools/artifact_check.py` and
  the close-time check exit-2s; the workaround: a manual copy that
  passes ruff
- the scaffold: src/rumpun/scaffold.py — what `rumpun init` emits
- the fix per the issue's own workaround: the scaffold ships
  tools/artifact_check.py (a genuine tool that passes ruff)

## Task
1. Reproduce on current main: `rumpun init` a fresh campaign; check
   tools/ for artifact_check.py; run a harvest close; measure the
   error.
2. Branch per the evidence: fixed since 0.11.0 → close with evidence;
   still broken → the scaffold ships tools/artifact_check.py at init
   (the file is the checker itself, copied from the source tree at
   scaffold time — ruff-clean by construction), with pins
   (tests/test_s102_w2_pins.py, _s102w2_ prefix, offline): init
   emits the checker; the emitted file passes ruff; the harvest's
   close-time check finds it.
3. notes.md REQUIRED: the reproduction, the fix, the pin list.

## Bounds
- Edits: src/rumpun/scaffold.py, tests/. notes.md REQUIRED. The
  khursani campaign is read-only evidence.
