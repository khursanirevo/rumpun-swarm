# s48 w2 — notes: spec-first pins for the m5 repro re-seal

Worker: w2 (tests owner). Workspace: .rumpun/runs/s48/w2.
Repo: /mnt/data/work/rumpun @ main 25393c4 (clean at session start).

## Deliverable (in this workspace, graft targets in brackets)

- [tests/] `test_s48_w2_reseal_pins.py` — 130 lines, sha256 5d094cd0…;
  2 pins, `_s48w2_`-prefixed helpers, additions-only vs tests/ as-is.
  - pin 1 `test_s48w2_resealed_repro_passes_with_m5_contract`: the evidence repro
    s22/w1-repro-m5.py passes current main at the matrix PASS bar (exit 0 +
    "GREEN: N/N checks passed" signature) and still asserts the honest
    "failed" status in source.
  - pin 2 `test_s48w2_drift_row_retired_and_arming_honest`: audit-36's DRIFT
    row (s22/w1-repro-m5.py, aka repro_m5_failed_exit, "assumptions moved",
    WIN band on re-seal) + the honest mapping on main (status_exit_code:
    failed→1, completed→0) + the retirement condition (the repro passes at
    the PASS bar).
- [workspace] `notes.md` (this file).

## The drift, measured (why the audit's arming was honest)

The evidence repro s22/w1-repro-m5.py against current main:

- ✅ measured: exit 1, crash FileNotFoundError on rimba/s1/_season/state.json
  (/tmp/s48w2_repro_manual.err; same tail in /tmp/s48w2_pins.log via pin 1).
- Root causes, both assumption moves — not regressions:
  1. The s45 rename rimba/ → runs/: the repro still reads
     rimba/s1/_season/state.json after a run.
  2. The P27 preflight lint: the repro's fixture season carries no
     reads-bearing phase, so `season start` refuses before any agent spawns
     (stderr: "lint errors block season start (P27 preflight)").
- The M5 contract holds on main: ✅ measured, status_exit_code("failed") == 1
  and status_exit_code("completed") == 0; the suite's M5 pin
  test_season_all_agents_failed_maps_to_nonzero is green in the baseline
  suite. So the repro's red is assumption drift — audit-36's DRIFT
  classification was honest and the re-seal band was the correct arming.

## Measured red set (current code, main 25393c4)

- ✅ measured: the pins file alone — 2 failed in 1.44s (/tmp/s48w2_pins.log):
  - pin 1: "repro exited 1" + FileNotFoundError tail (rimba/…/state.json) —
    red because the repro is not yet re-sealed.
  - pin 2: same crash tail — red because the DRIFT row's retirement
    condition (the repro passes on main) does not hold yet.
  Both reds land at the returncode assert; every earlier assert passed
  (pin 1's source assert, pin 2's record/mapping asserts), so the red reason
  is the spec reason: the repro is not re-sealed.
- ✅ measured: baseline suite (tests/ as-is): 221 tests collected.
- ⚠️ expected: the combined run reports 223 total, 221 green, these 2 red.
  The measured result lands here when the background run reports.

## Flip condition (green)

w1's re-seal lands at .rumpun/ledger/evidence/s22/w1-repro-m5.py: the repro
then passes current main at the PASS bar and both pins go green with no
edits. Pin 1's source assert ('"failed"' in the script) blocks any
contract-dropping re-seal.

## Graft

Land test_s48_w2_reseal_pins.py in tests/ as-is. Additions-only: the 221
existing tests stay untouched, 2 added. Ruff: All checks passed (repo
config: line-length 100, target py310; run with --no-respect-gitignore).
