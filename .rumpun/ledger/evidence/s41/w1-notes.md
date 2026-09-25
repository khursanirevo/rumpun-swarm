# s41 w1 — harvest integrity: M4 full + write-order repair

## Shipped (src/rumpun/harvest.py, workspace copy)

- M4 full gate: `_is_terminal` (completed | failed | stopped_*, fail
  closed on unknown statuses). harvest_season reads
  engine.read_persisted_status and raises AkarError naming season and
  status before any id is consumed or row written. The running-season
  warning path is gone.
- s21 row-exists refusal kept as the second guard, message unchanged.
- Write order: akar record before the verdicts row. Already the main
  order since s21; kept, now documented in the docstring and a comment
  at the append call.
- Callers unchanged: signature untouched; cli passes the same arguments;
  --band/--observed flow into the row as before (suite pin 3218 green).

## Evidence (scratch/repro_output.txt, scratch/suite_output.txt, scratch/probe.txt)

- repro 1 PASS: running season raises AkarError naming s7 + running;
  s7-harvest absent from akar.declared_ids; no verdicts row.
- repro 1b PASS: unknown status "paused" refuses, fail closed; nothing
  consumed.
- repro 1c PASS: truth table: completed, failed, stopped_stall,
  stopped_operator, stopped_budget terminal; running, paused, "" not.
- repro 2 PASS: injected fault after append_record landed: record stays
  on the ledger as the recovery source, no verdicts row, AkarError
  surfaced unswallowed.
- repro 2b PASS: fault before the append: no record, no row, nothing
  stranded.
- repro 3 PASS: second harvest of a harvested terminal season refuses
  via the s21 guard ("refusing second harvest"); one record, one row.
- suite: 185/185 passed, exit 0, 64.7s, with PYTHONPATH pointing at the
  workspace src; scratch/probe.txt records rumpun resolving to the
  workspace copy under that PYTHONPATH.
- ruff: clean on harvest.py and the repro with --no-respect-gitignore,
  repo pyproject config (line-length 100).

## Notes for merge

- Running the suite regenerates logs/s18..s22 outputs and replay-matrix.md
  with fresh tmpdir paths and PIDs; the churn is pre-existing suite
  behavior, not a patch effect (diffs are paths and PIDs only).
- engine.read_status docstring still names harvest among the live-reader
  consumers; harvest now reads read_persisted_status. engine.py is out of
  w1 scope; update that sentence at merge.
- Retry after a fault between the appends: the id is consumed, the record
  is the recovery source, the row is re-added by hand (the s32 repair
  shape). The retry itself refuses via the akar duplicate check by design.

## Repro

    cd /mnt/data/work/rumpun
    .venv/bin/python .rumpun/rimba/s41/w1/scratch/repro_m4_harvest.py
    PYTHONPATH=$PWD/.rumpun/rimba/s41/w1/src .venv/bin/python -m pytest tests/ -q
