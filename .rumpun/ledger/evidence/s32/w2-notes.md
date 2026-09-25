# s32 w2 notes — spec-first pins for the band-mask guard

## Verdict

Pins 1 and 4a red against current code for the spec reasons. Pins 2, 3, and
4b green-guard. Real-repo suite: 145/145 green. Scratch suite with the five
pins: 2 failed (the red pins, by design), 148 passed, 0 skipped. Ruff clean.
src/ untouched by w2: scratch lint.py + audit.py sha-identical to the real
repo.

## Measured red set (git ddf7dd7, 2026-09-15)

| pin | spec | measured | verdict |
|---|---|---|---|
| 1 | modules_integrated + band lacking any of integration/integrated/suite/tests -> exactly one WARNING naming the sid | zero warnings (guard absent) | RED, in-spec |
| 2 | same season, band carrying tokens -> no new warning | zero warnings | GREEN, guard |
| 3 | other metric + vague band -> no warning (guard scoped to the integration metric) | zero warnings | GREEN, guard |
| 4a | compliant bands -> no recalibrate candidate (old F5 trigger met) | recalibrate candidate fired | RED, in-spec |
| 4b | warned band -> recalibrate candidate | recalibrate candidate fired | GREEN, guard |

Red reasons, from the suite tracebacks: pin 1 `assert 0 == 1` on the warning
count (guard absent); pin 4a `assert not True` on the recalibrate line (no
band gate). Full runs: `scratch/evidence/red-run.txt` (exit 1, "2 failed,
3 passed, 145 deselected") and `scratch/evidence/full-suite-current.txt`
(exit 1, "2 failed, 148 passed in 53.58s").

## Green gates

- Real repo suite: 145 passed, exit 0 (`suite-real-repo.txt`).
- Scratch suite (145 existing + 5 pins): 2 failed (pins 1 and 4a, by
  design), 148 passed, 0 skipped (`full-suite-current.txt`). The scratch
  copy grafts `.rumpun/akar` + `.rumpun/rimba/s15` for the corpus-runner
  and stream-replay tests (s31 precedent); no skips anywhere.
- Ruff (line-length 100, --no-respect-gitignore): exit 0 (`ruff-run.txt`).
- Interpreter probe: the venv imports rumpun from real src; scratch src is
  sha-identical, so the tested bytes are the same either way
  (`interpreter-probe.txt`, `probe_resolution.py`).

## Contract the pins carry (for w1)

- Guard predicate: metric modules_integrated + primary_change.expected_band
  holding none of integration/integrated/suite/tests -> exactly one WARNING
  naming the sid. Wording and case policy are w1's; the pins constrain the
  tokens as lowercase substrings only.
- Audit: the recalibrate candidate fires only when the old F5 trigger holds
  (>= 2 LOSS seasons with integrated >= 1) AND a band-warned season sits in
  the audited window (same predicate applied to each window season's musim
  yaml).
- The two red pins split across the two halves: w1 must land both the lint
  warning and the audit gate, or one pin stays red.

## Deliverables (all under w2/ workspace)

- `scratch/repo/tests/test_rumpun.py` — the 145 existing tests byte-identical
  (cmp at stat size against the repo original), then one junction newline
  (the original's last line was not newline-terminated) plus the s32 w2
  section with 5 tests. Exact appended bytes:
  `scratch/evidence/pins-section.py`.
- Evidence: `scratch/evidence/{suite-real-repo,red-run,full-suite-current,
  ruff-run,interpreter-probe}.txt` and `pins-section.py`.

## Protocol note

An interim suite run measured earlier pins before a helper hardening (assert
no lint errors, so the green guards cannot pass vacuously) and a file
rebuild; its numbers are superseded by the final run above. The rebuild
first used a wrong byte-offset truncation that cut one original assert line;
cmp against the original at its stat size caught it, a pristine cp + append
fixed it, and only the verified-rebuilt file produced the measured numbers.
Recorded in memory (verify-state-writes, tenth instance).

## Provenance

- git HEAD ddf7dd7; measured 2026-09-15.
- Repo original test file sha256
  338db4d807f94f14a3bb72d8541f9c3bbf47b127b7530fba0360d16f4ff8a69b —
  byte-identical prefix of the scratch file (cmp at 179695 bytes).
- lint.py b072641770f8892866f79b26530b1d7901f1e32af7f9fa776803f1e549c708e3,
  audit.py c776abaaa92a9ae2edafcdfe0aa2d68683812ebca86abb49bc3be485c683cb97
  — identical in both trees.
- Collection: 150 tests (145 existing + 5 pins); 0 skipped in every run.
