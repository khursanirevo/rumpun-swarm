# s105 w1 — issue #21: restore the writer lanes' tools

Writer lanes spawn with core tools stripped; the s13-era a1 died of
it; the recovery is an undocumented ToolSearch probe. Your lane: the
tools restored (or the strip corrected at the spawn site) and the
recovery documented.

## Ground truth (measured 2026-09-18)
- issue #21 (OPEN, filed post-pause): writer lanes spawn with core
  tools stripped; s13/a1 died of it; the recovery is an undocumented
  ToolSearch probe
- the spawn site: the engine's writer spawn (the route command, the
  claude flags — the --disallowedTools or the settings shape)
- the s91-s104 writers ran on fable routes with the full flag set —
  what did s13's a1 lack that these had? The divergence is the fix's
  evidence base.

## Task
1. Measure the divergence: the s13/a1 spawn shape (the season's
   records) vs the s91-s104 writer spawn shape (the working routes) —
   the exact delta that stripped the tools. The evidence first, the
   fix second.
2. Fix the smallest surface: the spawn site emits the tools the
   writers need (or the route template carries them) — the writers'
   ToolSearch-class recovery documented in the spawn docs or the
   scaffold notes (issue #21's ask).
3. Pins (tests/test_s105_w1_pins.py, _s105w1_ prefix, offline): the
   spawn shape carries the tools (the route template or the spawn
   command asserted); the s13/a1 divergence shape (a fixture writer
   with the stripped shape) refuses or corrects per the landed fix.
4. Verify: the pins green; the current writer routes unchanged in
   behavior (the s91-s104 writers' shape preserved).
5. Close issue #21 with the evidence (one live call, disclosed).
   notes.md REQUIRED.

## Bounds
- Edits: the spawn/route surface, tests/. notes.md REQUIRED. One live
  gh call (the #21 close). No live season spawns.
