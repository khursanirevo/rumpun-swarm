# s48 w1 notes — the m5 repro re-sealed to current main

## Deliverable
- `repro_m5_failed_exit.py` (this workspace) — the s22 m5 repro re-sealed
  to current main. Same three-part shape (finalize reclassification,
  status→exit mapping, e2e verb honesty), 23 checks, same usage
  (`python3 repro_m5_failed_exit.py <repo-dir>`), same fixture season
  (RUMPUN_YAML_FAIL + SEASON_DUAL, byte-verbatim from tests/test_rumpun.py,
  diff-checked). No src/ changes.
- Re-seal deltas, all evidence-driven (old repro run vs main captured at
  /tmp/s48w1/old_repro.out):
  1. rimba/ → runs/ workspaces and state reads (s45 layout rename).
  2. musim/ → seasons/, plus the seasons/ + ledger/ + runs/ project shape
     (tests' _write_proj).
  3. The s22 inline season yaml lacked a phase with non-empty reads —
     current falsify lint blocks season start at the P27 preflight. The
     fixture is now SEASON_DUAL verbatim; its execute node carries reads.
  4. Dropped the Part B hasattr skip (sealed to current main).
  5. New exit-2 lane: unexpected exceptions exit 2 (script error), so a
     moved assumption can never masquerade as a behavioral red
     (audit-36's "unknown cause" cannot recur).
- Route fail value: RUMPUN_YAML_FAIL's "false" (the task fixture) instead
  of s22's "cat {prompt} | false".
- Assertions per contract: fail-season start exits nonzero, recorded
  status "failed", both agents "failed"; status/show/stop verbs exit
  nonzero on the failed season; the control season exits 0, status
  "completed", status/stop verbs 0.

## ✅ Verified: the re-sealed repro passes against current main
- Command: .venv/bin/python .rumpun/runs/s48/w1/repro_m5_failed_exit.py
  /mnt/data/work/rumpun
- ✅ RC=0, GREEN 23/23 checks, 2875ms wall. Full log: /tmp/s48w1/new_repro.out.
- Fail season: start rc=1, status "failed", alpha/beta both "failed";
  status/show/stop verbs rc=1. Control season: start rc=0, "completed",
  status/stop verbs rc=0.
- ruff 0.14.10 `check --no-respect-gitignore`: clean, RC=0
  (line-length 100, py310 target from the repo pyproject).

## ✅ Verified: the DRIFT arming's classification is honest
- Old repro (.rumpun/ledger/evidence/s22/w1-repro-m5.py) vs current main,
  this session: RC=1 in ~0.8s — unhandled FileNotFoundError at
  rimba/s1/_season/state.json, its own stale path from the s45 rename.
  Its season yaml is additionally lint-blocked (falsify lint: no phase
  with non-empty reads) before the M5 mapping is reached. Log:
  /tmp/s48w1/old_repro.out.
- Not a regression, measured the same session:
  - the re-sealed repro is GREEN 23/23 against main (above);
  - tests pin test_season_all_agents_failed_maps_to_nonzero: 1 passed
    in 0.56s (node-ID pytest run; /tmp/s48w1/pin.out).
- audit-36's "unknown cause" resolved: the exit 1 was the unhandled
  FileNotFoundError (a crash, not a check failure); the old repro had no
  exit-2 lane to say so. The re-seal adds that lane.
- Old repro Part A on main: all six finalize cases logged correct
  statuses (failed/failed/failed/completed/completed/stopped_operator) —
  the engine's M5 finalize core never moved; only the repro's bindings
  moved.

## Gates
- Write readback: 341 lines; 18 checks.append sites holding 23 checks
  (the run's own "GREEN: 23/23" line is the count gate); fixtures
  diff-VERBATIM against tests/test_rumpun.py ×3
  (RUMPUN_YAML_FAIL, SEASON_DUAL, RUMPUN_YAML).
- Raw outputs under /tmp/s48w1/ (old_repro.out, new_repro.out, pin.out).
