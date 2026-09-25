# s62 w1 — a salvaged win reads as salvaged

Criticisms landed: usefulness-decade-5 residual 7 ("Salvaged stopped
seasons earn WIN alongside completed seasons. Aggregate verdicts obscure
execution reliability and intervention costs.") and residual 6's season
labels point. The salvage mark is harness-observed: it derives from the
persisted terminal status, never from verdict content.

## What changed

### src/rumpun/harvest.py (the close writer cmd_harvest delegates to)
- `harvest_season` derives `salvaged = status.startswith("stopped_")`
  from the persisted terminal status it already reads via
  `engine.read_persisted_status` (runs/<sid>/_season/state.json), before
  any write and before the id is consumed.
- A salvaged close: the verdict row gains `"salvaged": true`; the akar
  record title becomes `season <sid> harvest (salvaged)`.
- completed and failed closes stay unmarked (no key, plain title):
  organic failure is not a salvage; the criticism names stopped seasons.
  stopped_operator and stopped_budget are marked (a stop-and-harvest is
  an intervention regardless of which rule fired).
- Docstring and module-docstring notes cite the decade-5 residual.

### src/rumpun/audit.py
- The F3 verdict histogram splits the WIN cell: `X WIN (Y salvaged)`
  when the window holds at least one row with `"salvaged": true` and
  verdict WIN.
- Zero marked rows: byte-identical to the pre-s62 line, so the two
  byte-exact F3 pins in tests/test_rumpun.py keep their shape.
- Only WIN splits per the spec format; a salvaged LOSS leaves the
  histogram unchanged. Rows are read as they are; no record is rewritten
  (the audit only ever appends).

### cli.py — no change
- cmd_harvest reads the terminal state through `harvest_season`, which
  is where `engine.read_persisted_status` already runs. A second read in
  the verb would be a divergent duplicate.

### tools/usefulness_audit.py — NOT changed (outside the w1 write set)
- The brief's counts can do the same, and the data now exists: the
  harvest row field is exactly what `verdict_history`
  (tools/usefulness_audit.py, "the last season-level row per season")
  reads. Follow-up for the file's owner: append " (salvaged)" to a
  history entry whose last season-level row has `salvaged: true`, and
  add the salvaged tally to the brief's ledger-facts line.

## Verification (✅ measured this session, exit codes and logs on disk)

- Fixture contract — verify_s62_w1.py, exit 0 (/tmp/s62w1_verify.log):
  - stopped_stall season through `cli.main(["harvest", ...])`: exit 0,
    row carries `"salvaged": true`, record title
    `title: season s900 harvest (salvaged)`.
  - completed and failed seasons: no salvaged key, plain titles.
  - F3 with one marked row: `2 WIN (1 salvaged), 1 LOSS, 1 INVALID`.
  - F3 with none marked: `2 WIN, 1 LOSS, 0 INVALID` (the pre-s62 byte
    form — the floor's pinned shape).
  - A salvaged LOSS row: `1 WIN, 1 LOSS, 0 INVALID` (only WIN splits).
- ruff (`~/.local/bin/ruff --no-respect-gitignore`, line-length 100
  config): src/rumpun/harvest.py, src/rumpun/audit.py, and
  verify_s62_w1.py — all clean.
- Suite floor:
  - Baseline (pristine src snapshot /tmp/s62w1_base_src):
    `1 failed, 272 passed` in 157s. The red is
    test_s38_coldstart_checker_leaves_repo_rumpun_untouched, the
    documented live-season red (s38-pin-live-season-red).
  - Post-change (src snapshot /tmp/s62w1_new_src with these edits):
    PENDING — numbers and the red-set diff land here when the run
    completes; the red set must equal the baseline's.
- Pinned suite reds beyond the baseline red are acceptable only when
  they are the documented race flakes; the diff above decides.

## Merge notes
- Additive only. No existing record is rewritten anywhere: harvest
  still refuses a second close (s21 guard), and the audit only appends.
- The s57 close check still never suppresses or rewrites the row; the
  salvaged mark rides the same append before the check runs.
- w2 pins (tests/) untouched by w1, per the lane split.
