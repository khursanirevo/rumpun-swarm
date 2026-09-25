# s37 w2 — notes: spec-first pins for the cold-start checker

Status: ✅ pins shipped, red set measured, 175 baseline green, pins proven
green against w1's landed checker in a replica. All numbers below are
measured; evidence files live in `scratch/`.

## Shipped

- `tests/test_rumpun.py` (workspace copy): repo bytes + append. Prefix
  byte-identical to main (`cmp`-proven each assembly). sha256 `2b95398f…`,
  228,646 bytes. ruff 0.14.10 clean, `--no-respect-gitignore`, len 100.
- Three s37 pins, spec-first, additions-only:
  1. `test_s37_coldstart_checker_full_run_all_steps_pass` — full checker run
     exits 0, >=6 `\bPASS\b` markers, zero FAIL tokens (combined out+err).
  2. `test_s37_coldstart_checker_sabotaged_init_fails_naming_step` —
     `--init-target` a chmod 555 dir (uid 1001): nonzero exit, FAIL marker,
     failed step named (init). Never fakes the sabotage.
  3. `test_s37_coldstart_checker_leaves_repo_ledger_untouched` —
     `.rumpun/akar` sha256 map byte-identical around one full run.
- Checker invoked via subprocess with the repo venv python (`sys.executable`
  when the suite runs under `.venv`), `timeout=120`, no wall-clock asserts.
- Repo root via the s27 walk-up helper `_pin_repo_root()` (workspace and
  merged alike). Missing checker = `pytest.fail`, never a skip.
- `_S37_TIMEOUT_S = 120`, `_S37_STEPS = 6` constants; fragment kept at
  `scratch/s37-pins-fragment.py`.

## Red set (measured, against current code)

| run | result | evidence |
|---|---|---|
| repo baseline on main | 175 passed, 53.90s, exit 0 | `baseline-suite.txt` |
| copy full run (1) | 15 failed, 163 passed, exit 1 | `copy-suite-run.txt` |
| copy full run (2, post `_pin_repo_root` switch) | 15 failed, 163 passed, exit 1 | `copy-suite-run2.txt` |

Failure split (both copy runs, 178 items = 175 + 3):

- 3 = the s37 pins. Reason: `tools/coldstart_check.py is missing … a blocker
  to report, not a skip`, resolved at the real repo root. Intended red.
- 12 = pre-existing location artifacts, not regressions: the s25 pin plus 11
  usefulness tests resolve `tools/` via `parents[1]`, which from
  `.rumpun/rimba/s37/w2/tests/` points at the workspace. They pass at the
  repo location (baseline row). Additions-only leaves them untouched; the
  repo-location suite is the regression authority.

## Green proofs (replica `scratch/repl`)

Replica: fake `_pin_repo_root` markers (`pyproject.toml`,
`src/rumpun/report.py`, `.venv/bin/python` symlink), fake `.rumpun/akar`
(two records), `tools/` copies including w1's checker, sha256 `2ee025a6…`
(byte-identical to w1's workspace copy at copy time).

| proof | result | evidence |
|---|---|---|
| three pins vs real checker | 3 passed, 1.63s, exit 0 | `repl-pins-green.txt` |
| manual full run, timed | 6/6 steps PASS, exit 0, wall 0.465s | `green-demo.txt` |
| manual sabotage (`--init-target` read-only) | exit 1, `STEP 1 FAIL: rumpun init …`, PermissionError | `sabotage-demo.txt` |
| temp dir survives | scaffold + akar `2026-09-15_s1-harvest.md` + `2026-09-15_audit-1.md` + verdicts.jsonl WIN row + status completed | `/mnt/data/tmp/rumpun-coldstart-4_0e4a19` |

The 0.465s wall is real, not a stub of the checker: the log shows six
`run: (cd <temp> && python -m rumpun …)` subprocess invocations. The engine
completes a stub season that fast.

## Merge notes for the harness

- Merge w1's `tools/coldstart_check.py` and this tests file together: the
  pins fail (never skip) while the checker is absent from main.
- Pin 1 reads combined stdout+stderr; the checker logs `STEP N PASS` at
  INFO via `logging.basicConfig(level=logging.INFO)`. Green run carries no
  FAIL token.
- Pin 3 concurrency caveat: an akar write during the ~0.5s checker run
  trips the byte-compare. Run the suite without a concurrent harvest/audit.
- Pin 2 needs uid != 0 (suite runs as uid 1001) so chmod 555 binds; under
  root the checker would pass and the pin fails honestly.

## Environment note

`pytest -k` does not filter in this environment: `-k s37` ran all 178 items
(twice), and `--collect-only -k s37` lists all 178. Mechanism unconfirmed
(venv pytest 9.1.1). Use explicit node IDs.
