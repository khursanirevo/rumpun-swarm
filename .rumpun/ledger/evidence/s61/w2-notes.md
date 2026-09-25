# s61 w2 — notes: pins for the pipeline's truth

## Tree state during measurement

- Pins authored against HEAD `1dd951d` (src/ clean at session start; only
  `logs/` and `replay-matrix.md` harness noise).
- ~14:39, mid-session, w1's EXERCISE route landed uncommitted in the shared
  tree: `src/rumpun/engine.py` +40 lines. `_write_results` (engine.py:656,
  called at engine.py:772 inside `_finalize`, before the state commit) writes
  `runs/<sid>/results.jsonl` from the final snaps — unit, route, state,
  exit_code, seconds; sorted by unit; atomic tmp+replace. Rows carry no
  `verdict` key, so the s35 WIN-with-FAIL-units mismatch check is untouched.
- Consequence: the live-tree pins run measures the POST-change engine. The
  spec-first red set was therefore measured against a HEAD extraction
  (`git archive 1dd951d | tar -x -C /tmp/s61w2_head`; the copy's engine has
  0 hits for `_write_results`, the live file has 2 — checked before running).

## The pins (tests/test_s61_w2_pins.py, additions-only)

Every pin runs the real verbs (`season start` / `lint` / `audit`) as bounded
subprocesses over tmp `.rumpun` projects; each season stub carries a 1-minute
engine-side budget and S61W2_TIMEOUT=120 bounds every subprocess; the dead
stub self-exits at 91s. No pin touches the real repo, ledger, or seasons.

1. `test_s61w2_pipeline_truth_route_holds` — the either-route truth. A
   pipeline-declaring season runs end to end; if its ledger lands a non-empty
   results.jsonl, EXERCISE is live. Otherwise a pipeline-less yaml must lint
   with zero errors and start to a completed season (TRIM is live).
2. `test_s61w2_fresh_audit_does_not_rearm_phase_liveness` — the retirement.
   Two pipeline-declaring seasons run, one fresh `rumpun audit` reads the
   campaign. EXERCISE: no "exercise or trim phase execute" candidate and the
   F1 line counts the exercised seasons in the numerator. TRIM: a pipeline-less
   yaml lints clean, and a campaign rebuilt on trimmed seasons audits with no
   phase-liveness candidate.
3. `test_s61w2_falsify_gate_still_guards_declared_writes` — no regression. A
   declared write with no reachable reader (evaluate reads measurements.jsonl,
   nothing writes it) must lint-fail with `falsify_required` in the refusal.
4. `test_s61w2_stall_record_shape_untouched` — no regression. A dead-stub
   season (0.1-minute stall window) must end stopped_stall with the s60
   `stall_stop` record: rule text, stall_s matching the season's, per-agent
   `sources == {}`, `tool_use_count is None`, `ws_bytes` int, and a finite
   `last_progress_age_s >= stall_s`.

## Measured red set — HEAD 1dd951d extraction (/tmp/s61w2_head)

Run: 2 failed, 2 passed in 7.99s (pytest exit 1). Log: /tmp/s61w2_pins_head.log

- pin 1 — RED, right reason: the season completed (agent exited 0) but left
  no ledger artifact, and the pipeline-less yaml was then refused at lint:
  `methodology.pipeline must be a non-empty list of nodes`. Neither route's
  truth held at HEAD.
- pin 2 — RED, right reason: after two completed seasons and a fresh audit
  that ran clean, the TRIM half's pipeline-less yaml was refused at the same
  lint gate. (Campaign A's fresh-audit record at HEAD was read but its
  candidate arming was not separately asserted; audit-41's arming on the real
  campaign is the ledger-recorded evidence for that half.)
- pin 3a — GREEN at HEAD: the falsify gate refused with `falsify_required`
  in the stderr. Guard holds pre-change.
- pin 3b — GREEN at HEAD: the s60 stall_stop shape held end to end.

## Measured green — live tree (w1's change landed)

Run: 4 passed in 7.83s (pytest exit 0). Log: /tmp/s61w2_pins_live.log

- pin 1 holds on the EXERCISE branch: results.jsonl lands non-empty at the
  season ledger (observed in the kept fixture: rows are the final agent
  snaps, e.g. `{"unit": "w1", "route": "stub", "state": "exited",
  "exit_code": 0, "seconds": 0.0}`).
- pin 2 holds on the EXERCISE retirement: solo re-run with live logs printed
  `EXERCISE retirement held: F1 counts 2 of 2` — the fresh audit carried no
  phase-liveness candidate and the F1 line counted both exercised seasons.
- pins 3a/3b green: the guards hold alongside the landed change.

A discarded earlier run (~14:39, /tmp/s61w2_pins_red.log) predates the pin-3b
NameError fix in this file and is not evidence.

## Tooling verdicts

- ruff clean: `~/.local/bin/ruff check --no-respect-gitignore --config
  "line-length = 100" --select E,F,I,UP,B,SIM,RUF --target-version py310
  <file>` — All checks passed. (Repo .venv has no ruff.)
- py3.10+ syntax (ruff target-version py310 enforced); stdlib + pytest only;
  logging, never print.

## Repro

```
cd /mnt/data/work/rumpun
.venv/bin/python -m pytest .rumpun/runs/s61/w2/tests/test_s61_w2_pins.py -v
# red side (pre-change src):
rm -rf /tmp/s61w2_head && mkdir -p /tmp/s61w2_head
git -C /mnt/data/work/rumpun archive 1dd951d | tar -x -C /tmp/s61w2_head
cp .rumpun/runs/s61/w2/tests/test_s61_w2_pins.py /tmp/s61w2_head/tests/
cd /tmp/s61w2_head && /mnt/data/work/rumpun/.venv/bin/python -m pytest tests/test_s61_w2_pins.py -v
```

## Merge notes for the harness

- Graft `tests/test_s61_w2_pins.py` into tests/ as-is; the `_s61w2_` prefix
  collides with nothing. The pyproject walk-up in `_s61w2_root` works from
  both locations (workspace and tests/).
- Pins are green at merge on the EXERCISE route w1 landed. The TRIM branch is
  the alternative-route holder: measured red at its first assertion at HEAD;
  its downstream (trimmed-campaign audit) never executed on the live tree.
- Guards (3a/3b) are green-by-design pins: green at HEAD and green on the
  landed tree — the season must keep them green.

## Suite floor

Launched against the live tree (py_compile probe passed first). Result
appended below on completion.

Log: /tmp/s61w2_suite.log
