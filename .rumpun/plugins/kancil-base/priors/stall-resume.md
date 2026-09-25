# Judge stall on durable progress, resume from the salvage

## The prior

Stall detection keys on harness-observed durable progress: new artifact
content, appended bytes, accepted checkpoint, state transition. Heartbeats,
repeated log lines, and file mtimes do not count. Liveness (a process that
exists) is not progress. A stalled unit is stopped on that evidence, and
the work resumes from the last accepted checkpoint or the recorded
salvage, never from zero.

## Why this holds

The classic bug: a stall rule that measured runtime instead of progress
killed writers that were mid-write; the fix shipped with a regression
test, and the killed season's salvage seeded the landing. The inverse bug
is as real: a writer frozen mid-write looks alive to any liveness check.
Appended bytes and new artifact content are the signals that survive
both.

## How to apply

- Size the stall window to the task; one window does not fit all writes.
- Detection thresholds ship with a regression test, always.
- After a stop, harvest the salvage first; the next attempt starts from
  it.
