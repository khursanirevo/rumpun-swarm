# s35 w2 notes — spec-first pins for the verdict-consistency cross-check

## Verdict

Five pins, additions-only (5730 bytes appended after the byte-identical
prefix): three red-checked against current code, two green-guards. Real-repo
suite: 166/166 green, exit 0. Scratch suite (171 = 166 + 5) against current
code: 3 failed (the red pins), 168 passed, 0 skipped, exit 1. Ruff: the
appended scratch file's findings are identical to the real repo file's under
the same invocation (one pre-existing I001; the section adds zero findings).
Real src/ and tests/ untouched by w2; every write sat inside the workspace
and every mutating call was readback-verified (four write corruptions caught
and rewritten in small chunks; evidence kept).

## Measured red set (git ed36835, 2026-09-15)

| pin | test | spec | measured reason |
|---|---|---|---|
| 1 | test_verdict_mismatch_arms_one_candidate_citing_season_and_unit | WIN season + FAIL unit row -> exactly one candidate citing the season and the failing unit; the passing unit is never cited | RED: "expected exactly one candidate, got: []" |
| 2 | test_verdict_consistent_season_arms_nothing | all-WIN unit rows under a WIN season -> zero candidates | GREEN-guard: vacuous today; guards over-trigger post-merge (e.g. WIN rows counted as mismatches) |
| 3 | test_verdict_mismatch_needs_result_rows | zero unit rows -> zero candidates, no crash; the absent-file path rides the base fixture's empty s2 | GREEN-guard: vacuous today |
| 4 | test_verdict_mismatch_multiple_fail_rows_one_candidate | N FAIL rows -> still exactly ONE candidate citing every failing unit | RED: "expected one candidate, got: []" |
| 5 | test_verdict_mismatch_outranks_residuals_for_cap | mismatch outranks usefulness residuals for the cap-3 slots | RED: "mismatch missing or duplicated: [residual one/two/three candidates]" |

Red run: `3 failed, 168 passed, 0 skipped` (evidence/red-run.txt, exit 1).
All three reds fail for the spec reason: zero mismatch candidates armed;
pin 5's log shows the three residual candidates taking the whole cap.

## Contract the pins carry (for w1)

- Trigger: a season's verdict (the last verdicts.jsonl row whose `season`
  value is the sid — the same season-level rule F5 already reads) is WIN
  while a results.jsonl unit row of the same season carries verdict exactly
  "FAIL".
- Arms: exactly ONE candidate per season regardless of FAIL-row count; it
  cites the season id and every failing unit; passing units are never
  cited (pin 1 asserts the passing unit's name is absent).
- Placement: mismatch proposals must enter the proposal list BEFORE the
  usefulness-residual loop (pin 5). The real ledger carries 60+ residual
  proposals, so a mismatch appended after that loop is always capped out
  of real audits — the candidate would never reach the evolve gate.
- Wording freedom: the exact candidate template is w1's choice; pins
  assert the "candidate:" prefix, the sid, and the failing-unit names.
  A finding line for the mismatch is also w1's freedom; pins assert
  candidates only.
- Scope boundary: the cross-check keys on verdict == "FAIL" exactly; WIN
  unit rows arm nothing (pin 2). Whether LOSS/INVALID season verdicts or
  non-FAIL unit verdicts cross-check too is unpinned — w1's choice, not
  asserted either way.

## Green gates

- Real repo suite: 166 passed, exit 0 (evidence/repo-suite-probe.txt).
- Scratch suite, current code (166 + 5 pins): 3 failed (the red pins),
  168 passed, 0 skipped, exit 1 (evidence/red-run.txt — one run is both
  the measured red set and the 166-stay-green regression gate; 168 =
  166 existing + the two green-guard pins).
- Byte gates on the append: prefix cmp identical for the first 209549
  bytes (the repo file), suffix cmp identical for the 5730 appended
  bytes; evidence/pins-section.py is the exact appended bytes; scratch
  file sha256 9a57b28e1f629224de5d6dae1a1928292a72aac330cc8fbd700bad971a826cfe,
  215279 bytes, 171 collected.
- Interpreter probe (evidence/interpreter-probe.txt): the venv default
  resolves rumpun from real src; the red run pinned
  PYTHONPATH=<scratch>/repo/src and the src .py trees are byte-identical
  (evidence/src-identity.txt), so the red set measured current bytes
  either way.
- Ruff (line-length 100, repo config, --no-respect-gitignore):
  evidence/ruff-run.txt — zero new findings.
- Grafts replicate the s34 recipe: .rumpun/akar/evidence plus
  .rumpun/rimba/s15/{w1,w2}/agent.log into scratch/repo/.rumpun/ (the
  real-stream tests pass, 0 skipped in the definitive run).

## Deliverables (all under w2/)

- scratch/repo/tests/test_rumpun.py — repo file (209549 bytes,
  sha256 9c9a58c3b1a754559bd968b7a070d41a64f0df46ce517fd2edaa712ef5c205a9)
  plus the pins section, additions-only.
- scratch/evidence/ — pins-section.py (exact appended bytes), red-run.txt,
  repo-suite-probe.txt, ruff-run.txt, interpreter-probe.txt,
  interpreter_probe.py, src-identity.txt.
- notes.md — this file.
