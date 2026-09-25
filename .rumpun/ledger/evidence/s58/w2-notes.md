# s58 w2 — spec-first pins for the epic rollup: notes (2026-09-16)

Spec anchors: the season goal (.rumpun/seasons/s58.yaml: "the campaign's
arcs become data ... rumpun epics renders the rollup - verdict counts and
season spans derived from the records, the records themselves
byte-identical, never merged"), w1's brief
(.rumpun/prompts/dev/w1-epics.md), operator directive seq 5 (epics as
DATA; records stay append-only and byte-identical), and ledger records
2026-09-16_s56-harvest + 2026-09-16_audit-40 (the rollup reads what
harvest writes). Precedent file: tests/test_s56_w2_pins.py (subprocess +
bounded-run + _-prefixed helper shape).

## Deliverable

.rumpun/runs/s58/w2/tests/test_s58_w2_pins.py — 5 pins, additions-only,
`_s58w2_` helpers, py3.10+, ruff clean at line-length 100, no prints,
no rumpun imports (subprocess and file reads only). Graft: land this file
in repo tests/ as-is.

- pin 1  test_s58w2_epics_rolls_up_two_declared_epics        (spec 1 + spec 3 honesty clause)
- pin 2  test_s58w2_duplicate_membership_lints_out           (spec 2)
- pin 3  test_s58w2_member_without_season_yaml_lints_out     (spec 2)
- pin 4  test_s58w2_missing_epics_yaml_hints_and_exits_zero  (spec 3)
- pin 5  test_s58w2_verb_and_init_leave_ledger_byte_identical (spec 4)

## Interface contract the pins hold

`rumpun epics [--init]`, cwd inside the campaign (the verb resolves the
project from cwd like every verb). Declaration at .rumpun/epics.yaml:
mapping epic id -> {title, goal, seasons: [...]}. Verdicts are read from
harvest's own books, nowhere else: the season-level rows in
.rumpun/runs/<sid>/verdicts.jsonl ({"season", "verdict", ...} — the M3
row shape) and run state from .rumpun/runs/<sid>/_season/state.json.
Rendering: one stdout line per epic — id, span (min-max member ids),
rollup "X WIN / Y LOSS / Z other" (NEUTRAL/INVALID fall into other), and
the title. A member with no run state contributes no verdict and marks
its epic's line with "no state". Missing epics.yaml: flat stdout hint
naming epics.yaml, exit 0. Duplicate membership: nonzero exit naming the
season and both epics. Member without a season yaml: nonzero exit naming
the member.

Surface assumptions (from established verb conventions, documented for
the merge):

- Rollup lines render to stdout (print — the season-list /
  direct --list / models convention). Pin 1 counts lines on stdout only.
  Refusals may log to stderr, so pins 2 and 3 match their tokens on
  stdout+stderr combined.
- The epic lint rules surface through the `epics` verb itself
  (lint-gated rendering, the season-start preflight pattern; w1's brief
  puts the rules on the declaration deliverable). The pins hold the
  observable contract — nonzero exit plus names — not any lint.py entry
  point, so either wiring satisfies them.

## Measured red set (all measured, none projected)

Two snapshots, both measured.

Snapshot P — pristine clone of HEAD 1737437 (git clone; probe
/tmp/s58w2_probe.py confirms rumpun resolves to clone/src ahead of the
editable install): **5 failed in 0.89s** (/tmp/s58w2_pins_pristine.log).

| pin | spec | outcome | measured reason (pristine) |
|---|---|---|---|
| 1 rollup | spec 1 | RED | `rumpun epics` exits 2 — argparse "invalid choice: 'epics'": no verb, so no rendering exists |
| 2 dup | spec 2 | RED | the rc!=0 gate passes (exit 2) but the argparse usage text names neither s63 nor epic-a/epic-b: no lint rule exists |
| 3 no-yaml | spec 2 | RED | same shape: usage text never names s99 |
| 4 hint | spec 3 | RED | exits 2 and renders no hint; the rc==0 assertion fails |
| 5 immutability | spec 4 | RED | the verb leg exits 2 before any digest comparison; no --init exists to hold immutability |

Snapshot L — the live tree: clean at HEAD 1737437 when measured (empty
`git status`; w1 had landed nothing in src/ at measurement time); solo
run identical: **5 failed in 0.70s** (/tmp/s58w2_pins_live.log).

## Merge gate

[fill on suite completion]

## Verification

- ruff: `~/.local/bin/ruff check --no-respect-gitignore --line-length
  100` on the pins file -> All checks passed (ruff 0.14.10).
- Interpreter: repo .venv python (3.13.12), pytest 9.1.1; PYTHONPATH
  pinned to the tree under test ahead of the editable install (probed).
- The real campaign ledger was never written by any pin: every pin runs
  inside tmp_path fixtures; the verb runs carry cwd pointing at the
  fixture, never the repo.
- No transient copy remains in repo tests/ (graft is the harness's job;
  my only tests/ write is inside the workspace).

## Logs (all outside the repo)

/tmp/s58w2_pins_pristine.log (pristine red set), /tmp/s58w2_pins_live.log
(live red set), /tmp/s58w2_probe.py (import-resolution probe),
/tmp/s58w2_baseline.log + /tmp/s58w2_full.log (merge-gate suite runs),
/tmp/s58w2_suite_done.marker (suite chain completion signal).
