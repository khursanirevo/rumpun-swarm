# s49 w2 - spec-first pins for the superseded-repro skip

## Shipped
- pins/test_s49_w2_pins.py (287 lines, 3 tests, additions-only:
  a new file; no existing suite file touched).

## Spec reconciled
- audit-37 re-proposes the candidate every audit:
  "candidate: drift mismatch: s22/w1-repro-m5.py - assumptions moved
  (...); band: WIN when s22/w1-repro-m5.py is updated or re-sealed to
  current main behavior".
- s48-harvest rules it already paid: "the re-seal landed" at
  evidence/s48/ (w1-repro.py), "and the drift row is retired".
- tools/replay_corpus.py still carries the s22/w1-repro-m5.py adapter
  (ADAPTERS) and re-runs it each corpus run (exit 1 -> DRIFT row);
  src/rumpun/audit.py arms the drift-mismatch candidate from DRIFT
  rows (one per script, matrix order).

## Pins (pins/test_s49_w2_pins.py)
1. test_s49w2_m5_row_is_skip_citing_the_s48_reseal: the m5 row is
   SKIP and its note cites s48 + supersed/re-seal. Red today.
2. test_s49w2_audit_after_skip_has_no_m5_drift_candidate: run_audit
   on the s30 fixture ledger fed the REAL fresh matrix carries zero
   "drift mismatch:" candidate lines. Red today.
3. test_s49w2_other_five_repros_still_pass: the five non-m5 adapters
   stay PASS in the same fresh matrix (holdfast, green today).
4. Regression duty: out-of-band suite evidence (sections below); no
   test runs the suite from inside itself (s30 pin-5 precedent).

## Measured red set (head 6876de8, clean worktree, pytest 9.1.1)
Command: python3 -m pytest .rumpun/runs/s49/w2/pins/test_s49_w2_pins.py -q
(under the repo venv, from the repo root). Log: /tmp/s49w2-pins-red.txt.
Result: 2 failed, 1 passed in 21.80s.
- pin 1 red, right reason: the m5 row is
  ('DRIFT', 'exit 1 in 5.9s; aka repro_m5_failed_exit; assumption
  moved: unknown cause (see logs); see logs').
- pin 2 red, right reason: candidates carry
  'candidate: drift mismatch: s22/w1-repro-m5.py - assumptions moved
  (...); band: WIN when s22/w1-repro-m5.py is updated or re-sealed to
  current main behavior' - byte-identical in head to audit-37's
  re-proposed candidate (positive control).
- pin 3 green (holdfast).

## Pre-existing red at HEAD (measured, not touched: additions-only)
- tests/test_s43_w2_pins.py: 3 of 8 red at HEAD
  (test_fresh_matrix_coverage_finding_counts_all_rows,
  test_coverage_gap_is_finding_never_candidate,
  test_coverage_zero_pass_is_honest). They expect a
  "corpus coverage: N of M discovered (K SKIP)" finding;
  grep finds zero "coverage" hits in src/rumpun/audit.py - the
  feature never landed. Standing red spec-pins, unrelated to s49.
- test_stop_racing_spawn_tracks_and_kills_every_spawn: red under
  full-suite runs ("w2 ran, no marker"), GREEN solo (measured:
  /tmp/s49w2-solo2.txt, 1 passed). Concurrency/timing-sensitive.
- test_s38_coldstart_checker_leaves_repo_rumpun_untouched: red in
  every run while an s49 agent session is active. Its own failure
  names the deltas: changed=['.rumpun/runs/s49/w2/agent.log',
  '.rumpun/runs/s49/w2/state.json'] - this session's harness files,
  not checker mutations. Environmental; passes on a quiet tree.

## Suite evidence (pin 4, regression duty)
- Baseline full tests/ dir (221 tests, concurrent with pin writing):
  4 failed, 217 passed - the 2 session-noise reds above plus the 3
  s43 coverage reds; log /tmp/s49w2-suite-baseline.txt.
- tests/test_rumpun.py alone (the 188, sequential, quiet):
  2 failed, 186 passed - exactly the 2 session-noise reds above;
  log /tmp/s49w2-suite188.txt. The other 186 green.
- Solo node run of the 2 reds: 1 failed (s38, environmental) +
  1 passed (stop_racing); log /tmp/s49w2-solo2.txt.
- Verdict: the 188 stays green modulo the 2 known
  session-environment reds, both diagnosed above with the failure
  output as evidence; neither is touched by the s49 pins.

## Ruff
ruff check pins/test_s49_w2_pins.py -> All checks passed! (rc 0),
repo config line-length 100, py310.

## Handoff to w1 (pinned interface)
- The matrix must carry the m5 row as SKIP, note citing s48 and
  supersed/re-seal (pin 1 wording latitude is deliberate).
- Post-skip ingestion must arm zero drift-mismatch candidates from
  the fresh matrix (pin 2); audit.py's drift arming itself is
  unchanged (the s43 drift-arming pins keep passing).
- Pin 3 guards the five other adapter rows staying PASS.
