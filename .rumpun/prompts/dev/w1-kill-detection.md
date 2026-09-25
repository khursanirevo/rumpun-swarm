# s92 w1 — fix the kill-detection gap (the s91 disclosure)

A writer killed by the OOM was recorded as exited 0, and the stall
watcher stayed silent for 20 minutes. The engine must not lie about
its writers.

## Ground truth (measured 2026-09-17)
- s91 w1 was killed mid-verification at 22:23 (the workspace frozen,
  no notes.md, the exit file 1 byte); the engine recorded
  "exited code 0" and ran on for 20 more minutes
- the engine: src/rumpun/engine.py — the spawn wrapper writes the
  exit file after the pipeline completes; a killed claude inside the
  pipeline leaves the wrapper's rc ambiguous
- the stall watcher: the tool-activity/workspace-growth clocks (the
  s60 fix) — they did not fire for w1

## Task
1. Reproduce: kill a spawned writer's claude process mid-run (a
   fixture spawn + kill); measure what the engine records (the exit
   file, the state) and when the stall clock would fire.
2. Fix the smallest surface: the wrapper's exit recording must
   distinguish a real exit from a signal death (rc >= 128 = signal),
   and the engine records it honestly (killed -> the killed state,
   not exited 0). The stall watcher's clocks: verify why they stayed
   silent (a silent writer with a growing log is not idle — if the
   log-growth clock should have caught it, fix that clock).
3. Pins (tests/test_s92_w1_pins.py, _s92w1_ prefix, offline): a
   killed-writer fixture records the killed state; the exit file
   distinguishes rc 0 / rc 1 / signal death; the stall clock fires
   on a log-growing silent writer.
4. notes.md REQUIRED: the repro, the leak, the fix, the pin list.

## Bounds
- Edits: src/rumpun/engine.py, tests/. notes.md REQUIRED. No live
  season spawns in pins (fixtures only).
