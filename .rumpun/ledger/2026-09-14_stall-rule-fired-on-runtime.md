# akar record: stall-rule-fired-on-runtime
id: stall-rule-fired-on-runtime
date: 2026-09-14
title: stall rule killed healthy spawns; hot-fixed to progress-based
finding: the stall stop rule measured runtime, not progress

engine.py _agent_snap marked a live spawn stalled when
time.time() - started_at > stall_s — runtime since START. The module
contract (and the rule's name) promise stall = no durable progress for
stall_minutes. Any healthy spawn living past stall_minutes was killed
mid-work at exactly the threshold.

victims: s3 (stopped_stall), s14/w2 (terminated at 900s), s15/w1 and
s15/w2 (terminated at 900s while actively streaming — w1's log grew
until 3s before the kill; its last Bash result read skeleton3-written).

hot-fix (harness-built, bwrap-workaround precedent: infrastructure that
kills seasons is repaired by the harness and cited, not re-run):
stalled now requires no agent.log growth for stall_s
(last progress = max(started_at, log mtime)). Regression test
test_agent_snap_stall_tracks_log_progress_not_runtime pins both sides;
suite 55/55 after fix.

note: default stall_s stays 2700s; seasons declaring
stall_minutes: 15 now mean it honestly. Seasons killed by the old rule
were not stalls and their LOSS verdicts stand on their own bands; the
s15 spawns never exited, so no-exit artifacts were impossible.

sha256: 23841df1c62bcff6811e8a105e682350ff6d8bf885e0d8294e38c6b7465c5bdf
