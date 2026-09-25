# s61 w1 — the pipeline tells the truth (audit-41 candidate)

## Route chosen: EXERCISE

Evidence that decided it:

- results.jsonl is a regression, not a missing feature: files exist for
  s2-s50 (harness-authored merge rows: `unit`, `verdict`, `integrated`,
  `verdict_detail`), then stop at s51. audit-41 shows 0 of 10 in s51-s60.
- No code ever produced it: grep over src/rumpun shows results.jsonl only
  in audit.py (readers: F1 existence, F5 integrated, s35 mismatch) and
  scaffold.py (declarations). The historical producer was the operator's
  merge habit, outside the codebase, which stopped landing rows at s50.
- evaluate->verdicts.jsonl is 10/10 live for the same reason verdicts.jsonl
  is real: harvest_season writes it harness-side at close (M3). The
  accepted system truth is "phase artifacts are written at close";
  results.jsonl just lost its producer.
- EXERCISE restores the contract without inventing judgment: the close
  writes what it observed. TRIM would retire a finding that caught a true
  ten-season gap AND strip the falsify gate's substrate (the gate reads
  the pipeline's writes set; the constraint says the gate stays intact).

## The change (src/rumpun/engine.py, minimal)

- New `_write_results(root, sid, snaps)`: at close, writes
  `.rumpun/runs/<sid>/results.jsonl` (season dir root, where audit's F1/F5
  readers already look) from the final snaps only: `unit`, `route`,
  `state`, `exit_code`, `seconds`, sorted by unit. Rows carry NO `verdict`
  key (that is a judgment; the s35 WIN-with-FAIL-units check is therefore
  untouched) and no `integrated` key (F5 semantics preserved).
- Called inside `_finalize`'s state lock, BEFORE `_save_state`: state.json
  is the commit point; a crash between the two writes leaves the season
  running and the re-finalize rewrites the file deterministically (atomic
  tmp+replace). First finalize wins, so one write per season.
- lint.py, audit.py, harvest.py: untouched. Falsify gate and the s60 stall
  record untouched. Tests untouched (w2 owns the pins).

## Verification

✅ VERIFIED REAL: stub season s999 (writer exits 0) completes; the close
left `{"unit": "w1s", "route": "stub", "state": "exited", "exit_code": 0,
"seconds": 1.0}` at scratch/.rumpun/rimba/s999/results.jsonl. Runner:
scratch/run_stub.py, exit 0.
✅ VERIFIED REAL: stub season s998 (stall_minutes 0) closes stopped_stall;
results.jsonl carries the terminated row AND state.json keeps the intact
s60 stall record (rule + per-agent sources). Same runner, exit 0.
✅ VERIFIED REAL: the audit's own F1 function over the scratch campaign
reads `phase execute (writes results.jsonl) wrote its artifact in 2 of 2
engine seasons (s998,s999)`. Runner: scratch/run_audit_probe.py, exit 0.
✅ VERIFIED REAL: suite floor. Baseline before the change: 1 failed, 268
passed; the one red is test_s38_coldstart_checker_leaves_repo_rumpun_
untouched (documented live-season red). After the change: 1 failed, 268
passed, the same single red. Delta zero. Logs: /tmp/s61-w1-baseline-suite.log,
/tmp/s61-w1-postsuite.log.
✅ VERIFIED REAL: ruff clean on engine.py and both scratch runners
(~/.local/bin/ruff, --no-respect-gitignore).

Not verified: the stopped_operator path (stop_season) goes through the
same _finalize funnel; not separately exercised. The operator merge can
still append rich rows (verdict/integrated) to the close-written file.

## Residuals for the harness

- w2's future pins can drive the real engine end to end and read
  results.jsonl at close (the s999/s998 stub shapes are the templates).
- The candidate's WIN band is met by construction for future seasons: a
  later season's ledger holds results.jsonl at close.
