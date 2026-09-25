# s21 w2 — L2 barrier in the dual-start test + M3/M11 pins

## Measured results

- Red set against base 8011004 (scratch/base tree: git archive of the base
  commit + this workspace's test file, base src forced via PYTHONPATH):
  2 failed, 1 passed — M3 red on `harvest must write rimba/<sid>/verdicts.jsonl`,
  M11 red with the `<model>` command captured verbatim, M4-minimal refusal
  green. Captured: `scratch/red-base.txt`.
- Current tree (w1's harvest.py/routes.py landed mid-flight, uncommitted):
  3/3 pins green. Full suite: 103 passed in 31.49s, exit 0 — the 100
  pre-existing tests (99 kept + the L2 test now deterministic) and all 3 new
  pins. Captured: `scratch/suite-main.txt`.
- Dual-start barrier: 5 consecutive green runs in the scratch tree, 1.3-1.4s
  each, plus a green suite-embedded run. Captured: `scratch/dualstart-5x.txt`.

## L2 barrier design

The review's literal shape (starter 1 parked inside the spawn transaction)
is impossible against this engine: the spawn-loop lock releases when the
loop ends (engine.py:593 with-block closes before the watch loop), and the
reattach path is write-silent — a starter that passes the finished check
leaves no filesystem trace. The test therefore proves both orderings from
outside:

1. Marker-gated route (`DUAL_BARRIER_ROUTE`, tests :481): agents block on a
   marker file, so the season cannot finalize while the test withholds it.
2. Starter 1 launches alone; the test waits until the flock-serialized spawn
   transaction has persisted both agent pids.
3. The test takes state.lock itself (probe). Starter 2 launches against it
   and is observed contending via /proc/<pid>/fd: the lock fd is open while
   the process is blocked — demonstrably contending, its spawned-alphas
   line not yet emitted.
4. Probe released; the test observes the lock fd close while starter 2 stays
   alive: it acquired the lock, passed the finished check against a season
   provably still running, and left the transaction.
5. Only then is the marker touched; both watchers finalize (first writer
   wins, second returns cleanly) and both exit 0.

Every original assertion kept: both exit 0, exactly one "spawned alpha"
line across both stderr streams, one terminal state.json with status
completed, alpha and beta once each in the spawned map, both workspaces
hold a state.json.

## Contracts pinned

- M3: after harvest_season on a completed WIN season, rimba/<sid>/
  verdicts.jsonl carries exactly one season-level WIN row (the row rule
  report._verdict_of reads: row["season"] == sid) and the report headline
  renders WIN.
- M4-minimal (green at base, measured): a second harvest refuses via the
  akar duplicate-id refusal, raised as akar.AkarError; one record remains.
- M11: every command write_routes writes has no <model> placeholder, passes
  /bin/sh -n with {prompt} resolved, and the scaffold lines survive the
  patch in order.

## Convergence note

w1's harvest.py/routes.py landed (uncommitted) while this workspace ran.
Measured against it: all three pins green — spec and implementation
converged before integration. The second-harvest refusal surfaces as
akar.AkarError (pin passes); whether it comes from harvest's own check or
akar's dup refusal is not distinguished by the pin.

## Anchors

- Review: .rumpun/akar/2026-09-14_codex-review-2026-09-14.md (M3, M11, L2).
- tests/test_rumpun.py: import fcntl :69; routes/scaffold import :90;
  DUAL_BARRIER_ROUTE :481; dual-start test :513; M3 pin :2493;
  M4-minimal pin :2523; M11 pin :2539.
- Captured outputs: scratch/red-base.txt, scratch/dualstart-5x.txt,
  scratch/suite-main.txt. Base tree: scratch/base.
