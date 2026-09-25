# s60 w2 notes — stall-progress pins

## anchors

- season goal: .rumpun/seasons/s60.yaml (WIN band names this file's three cases)
- w1 brief: .rumpun/prompts/dev/w1-stall-progress.md; w2 brief: w2-stall-pins.md
- ledger: 2026-09-16_s59-harvest (the s59 mid-write kill), 2026-09-16_audit-40
- deliverable: tests/test_s60_w2_pins.py (workspace tests/; graft as-is)

## the pins

Every pin drives the real engine end to end: `rumpun season start` as a
bounded subprocess over a tmp .rumpun project (the dual-start test's
pattern), one benih, a 0.1-minute stall window, a 60-second benih budget,
subprocess timeout 120s, dead stub self-exits at 91s. No wall-clock
assertions beyond the existing patterns (bounded polls; one floor assert
on the recorded age).

1. writer stub: silent stdout, one file/second, exits 0 at 12s — the
   season completes, agent exited 0, all 12 markers present, agent.log
   stays 0 bytes (no stream evidence existed). The s59 kill, negated.
2. dead stub: silent, writes nothing — still stalls: stopped_stall,
   terminated by the stall (no terminated_budget), agent.log 0 bytes.
3. dead-stub stop record: state.json carries top-level `stall_stop` —
   rule text, stall_s matching the season, per-agent
   `last_progress_age_s` finite and >= stall_s, `sources == {}` (no
   event of any class counted), `tool_use_count` None, `ws_bytes` an int
   (baseline recorded; growth would have stamped a source).

## measured red set (runs against the shared tree)

- Run 1 (13:47+08): 3 failed in 0.48s — WRONG-reason reds: lint refuses
  the fixture id `s60x` (season ids must match s<N>). Fixture defect,
  fixed to `s600`. Log: /tmp/s60w2-red.log.
- Run 2 (13:52+08): pins 1-2 PASSED, pin 3 FAILED — `stall_rule` absent,
  state keys carried w1's landed `stall_stop` instead. w1's engine change
  (file-write + tool_use progress) was already in shared src/rumpun/
  engine.py (158-line uncommitted diff) before my first clean run, so the
  spec-first red the brief expected for pins 1-2 was never observable;
  pin 1 passing is genuine: the engine counts the silent writer's file
  growth (mechanism read in the diff: _watched_bytes/_scan_agent_writes,
  tool_use stamping, absent stamps change nothing). Log: /tmp/s60w2-red2.log.
- Pin 3 re-pinned to the landed stall_stop shape (the brief's contract
  held; the shape follows w1's record).
- Run 3 (13:58+08): 3 passed in 26.70s. Log: /tmp/s60w2-green.log.
  ✅ verified real.

## surface assumptions

- Stop-record surface: the persisted state.json (durable), not the log
  line — w1's brief allowed either.
- Counted event classes read through per-agent `sources`
  (last_progress / last_tool_use / last_ws_progress stamps) and the
  counters; `sources == {}` is the honest empty count for a dead agent.
- The dead workspace's watched-bytes baseline is nonzero (~prompt bytes);
  pinned as "an int", not zero.

## floor

- engine.py py_compile OK; engine-adjacent subset 34 passed, 154
  deselected in 5.51s at 2026-09-16T14:04:10+08:00 against the tree
  carrying w1's uncommitted engine change (log: /tmp/s60w2-floor.log).
- Full-suite certification rides the harness merge; this file is
  additions-only, prefixed helpers, tmp_path fixtures, no shared state.
