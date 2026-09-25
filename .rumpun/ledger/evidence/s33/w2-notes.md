# s33 w2 notes — spec-first pins for the decadal usefulness audit

## Verdict

Nine pins red against current code for the spec reasons; one green-guard (pin
1b, vacuous pre-merge: with no decade trigger and no runner, a 9-season ledger
arms nothing trivially — it guards the negative case once w1 lands the
trigger). Real-repo suite: 150/150 green. Scratch suite (150 existing + 10
pins): 9 failed (the red pins, by design), 151 passed, 0 skipped. Ruff clean.
src/ and tools/ untouched by w2; the scratch src tree is sha-identical to the
real repo.

## Measured red set (git 4535ae4, 2026-09-15)

| pin | test | spec | measured red reason |
|---|---|---|---|
| 1a | test_usefulness_decade_finding_arms_at_ten_seasons | 10-season ledger arms "usefulness audit due for decade 1 (different-model review)" as a finding, never a candidate | `expected exactly one decade finding, got: []` — no decade trigger exists |
| 1b | test_usefulness_decade_finding_stays_silent_at_nine | 9-season ledger arms nothing | GREEN, vacuous pre-merge (nothing can arm at all yet); guard post-merge |
| 1c | test_usefulness_decade_finding_suppressed_then_decade_two | usefulness-decade-1 record suppresses decade 1; 20 seasons + that record re-arms decade 2 | decade-2 re-arm: `expected exactly one decade finding, got: []` (0 == 1) |
| 2 | test_usefulness_runner_appends_verdict_record_without_route_echo | stub route -> runner appends usefulness-decade-1 with verdict + residuals + evidence pointer; route echo never in the record | `runner exit 2; can't open file .../tools/usefulness_audit.py: No such file or directory` |
| 3a | test_usefulness_runner_missing_route_refuses_honestly | configured-but-absent route command -> nonzero, reason named, nothing invoked/appended | red at the named-reason assert: the can't-open-file stderr carries no "route" token (no runner exists to refuse) |
| 3b | test_usefulness_runner_failing_route_refuses_honestly | route exit 7 -> nonzero, "exit" + code named, marker proves invocation, nothing appended | red at named-reason assert, same missing-runner stderr |
| 3c | test_usefulness_runner_verdictless_route_refuses_honestly | exit-0 route with no verdict line -> nonzero, "verdict" named, nothing appended | red at named-reason assert, same missing-runner stderr |
| 3d | test_usefulness_runner_timed_out_route_refuses_honestly | route over usefulness.timeout_s -> nonzero, timeout named, wall < 15s, nothing appended | red at the timeout-reason regex, same missing-runner stderr |
| 4a | test_usefulness_residuals_arm_candidates_through_existing_machinery | a usefulness record's residual: lines arm candidates citing them | `expected 2 residual candidates, got: []` (0 == 2) |
| 4b | test_usefulness_residual_candidates_respect_cap | 4 residuals -> 3 candidates (MAX_CANDIDATES) + the dropped one in the unproposed line | `expected the cap to hold at 3, got: []` (0 == 3) |

Red run: `9 failed, 1 passed, 150 deselected` (scratch/evidence/red-run.txt,
exit 1). Full run: `9 failed, 151 passed in 55.32s`
(scratch/evidence/full-suite-current.txt, exit 1). Full per-pin tracebacks are
in both files.

## Green gates

- Real repo suite: 150 passed, exit 0 (scratch/evidence/suite-real-repo.txt).
- Scratch suite (150 existing + 10 pins): 9 failed (the red pins, by design),
  151 passed, 0 skipped (scratch/evidence/full-suite-current.txt). The scratch
  copy grafts .rumpun/akar + .rumpun/rimba/s15 (s31/s32 precedent); no skips.
- Ruff (line-length 100, --no-respect-gitignore, ruff 0.14.10): All checks
  passed, exit 0 (scratch/evidence/ruff-run.txt).
- Interpreter probe: the venv imports rumpun from real src
  (/mnt/data/work/rumpun/src/rumpun/__init__.py); scratch src is sha-identical
  (audit.py 97407cd6... in both trees), so the tested bytes are the same
  either way (scratch/evidence/interpreter-probe.txt).
- Stub scripts verified outside the runner (the red run never executes them):
  STUB_ROUTE_OK emits noise + 2 residuals + final verdict, exit 0, marker
  carries the prompt path; STUB_ROUTE_FAIL exits 7; STUB_ROUTE_NOVERDICT
  exits 0 without a verdict line; all four pass sh -n. Harness + outputs:
  scratch/tmp-stub-check/.
- Scratch test file: original 186020-byte prefix byte-identical (cmp),
  original sha 2c5a4253...; additions-only, 10 new tests, 160 collected.

## Contract the pins carry (for w1)

- Decade trigger (audit.py): season count = the FULL musim/s<N>.yaml count
  (not the last_n window). Trigger: floor(count/10) > number of
  usefulness-decade-* records in akar/ (record id or
  <date>_usefulness-decade-<N>.md filename). Finding text pinned:
  "usefulness audit due for decade <N>" + "(different-model review)" on the
  same body line, as a plain finding — never a "candidate:" line.
- Runner (tools/usefulness_audit.py): resolves the project from its working
  directory (cwd/.rumpun; no required flags — extra flags are w1's freedom).
  Config from <root>/rumpun.yaml: usefulness.route is a shell command string
  holding the {prompt} placeholder (same shape as every route in rumpun.yaml;
  the runner substitutes the temp prompt file path), usefulness.timeout_s
  hard timeout seconds, default 300. The record id is usefulness-decade-<N>
  with N = floor(full musim count / 10). The record carries: the verdict line
  text, the auditor's residual lines, and a pointer (the word "evidence" on
  some line) to the captured output stored under akar/evidence. The route's
  captured streams never enter the record.
- Honesty refusals (exit nonzero + stderr reason, nothing appended):
  - configured route command absent -> the message names "route";
  - route exits nonzero -> names "exit" and the code (pin 3b: code 7);
  - route omits the verdict line -> names "verdict";
  - route exceeds usefulness.timeout_s -> matches /time-?out|timed out/.
  The verdict line is the FINAL line carrying USEFUL / PARTIALLY USEFUL /
  SELF-LOOP DOING NOTHING. Residual lines: the runner parses lines starting
  "residual:" from the route output and carries their texts; the audit arms
  candidates from "residual:" lines in the usefulness record.
- Residual arming (audit.py): residual lines of usefulness-decade records arm
  candidates through the existing proposals machinery — each candidate cites
  its residual text; 4 residuals -> exactly 3 candidates + the dropped one
  named on an "unproposed here" line. Left to w1 (pins do not constrain it):
  whether older usefulness records retire once a newer one exists — pins 4a/4b
  use a single record. Placement/priority of residual candidates among the
  existing triggers is also w1's, as long as the cap and the unproposed line
  behavior hold.
- Fixture contract: _usefulness_proj shapes base as the repo root (DESIGN.md
  copied from the repo next to the .rumpun ledger — the runner and audit read
  the project under cwd; the real repo's root holds DESIGN.md + .rumpun/).
  The runner stub is a POSIX sh script because usefulness.route is a shell
  command string.

## Deliverables (all under w2/ workspace)

- scratch/repo/tests/test_rumpun.py — the 150 existing tests byte-identical
  (cmp at 186020 bytes against the repo original), then the s33 w2 section
  with 10 tests. Exact appended bytes: scratch/evidence/pins-section.py
  (349 lines, py_compile clean, 10 test functions).
- Evidence: scratch/evidence/{suite-real-repo,red-run,full-suite-current,
  ruff-run,interpreter-probe}.txt and pins-section.py; stub verification
  outputs in scratch/tmp-stub-check/ (marker, exit codes, sh -n runs).
- 10 new tests, 160 collected in the scratch suite.

## Protocol note

Three consecutive corrupted Writes this session (the Write tool carried the
corruption: interleaved duplicate fragments and unterminated strings in the
pins file). Caught on readback each time; the file was rebuilt via chunked
Bash heredocs with per-chunk readback, garbage-token grep, py_compile, and a
line-count ladder. Recorded in memory (verify-state-writes, eleventh
instance). No gate above rests on an unverified write.

## Provenance

- git HEAD 4535ae4df4978150deb0111134c54ad06cebf81f ("feat: s32 win ratifies
  band guard; s33 seeded"); measured 2026-09-15.
- Repo original test file sha256
  2c5a4253a627d133070180b249cb551c47686680fb0277dbe95c4b5a5833c3e1
  (186020 bytes) — byte-identical prefix of the scratch file.
- audit.py sha 97407cd6e8f024262b8c83bbdbbaa412e947fab38d02d5fcadf63ede864881c2,
  identical in the real tree and the scratch copy (src untouched by w2).
- Working-tree note: during the session the campaign harness wrote
  logs/*, replay-matrix.md, and .rumpun/musim/s34.yaml (the next-season seed);
  w2 wrote nothing outside w2/ (git status paths confirm).
