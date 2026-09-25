# s54 w2 — spec-first rename pins: notes (2026-09-16)

Spec anchors: seasons/s54.yaml goal + primary_change.expected_band;
ledger/directives.jsonl seq 3 (the rename confirmation); ledger records
2026-09-16_s53-harvest (s53 WIN, hub arc closed) and 2026-09-16_audit-38
(corpus green, no candidates); w1's prompt
(.rumpun/prompts/dev/w1-rename-finish.md) for scope calibration.
Precedent file: tests/test_s45_w2_rename_pins.py (helpers prefixed,
one-variable fixtures, red pins vs green guards marked).

## Deliverable

tests/test_s54_w2_rename_pins.py — 8 pins, additions-only, `_s54w2_`
helpers, py3.10+, ruff clean at line-length 100, no prints. Three green
guards, five red against current main (ed2eb17).

## Measured red set (solo, pre-merge, current main ed2eb17)

Command: PYTHONPATH=src .venv/bin/python -m pytest
.rumpun/runs/s54/w2/tests/test_s54_w2_rename_pins.py -q
Result: **5 failed, 3 passed in 3.99s**. Every red is for the spec reason.

| pin | outcome | measured reason |
|---|---|---|
| 1a both spellings lint clean | GREEN guard | zero errors both |
| 1b both spellings start identically | GREEN guard | both completed; roster alpha+beta same routes, exit 0; budget_s 180.0 both |
| 2a help sweep | RED | top help carries akar+tuai (harvest one-liner); evolve help carries akar (approve, rollback); audit help carries musim ("musim seasons") |
| 2b harvest one-liner names ledger | RED | line renders as `harvest  tuai: close a season into akar (step 4)` — no ledger |
| 2c reject stderr | RED | stderr carries akar+musim: cli `musim/rejected/; akar record` plus rumpun.akar's own `appended akar record` INFO line |
| 2d rollback stderr | RED | same shape: cli `season moved to musim/rejected/; akar record` plus the akar.py line |
| 3a draft_next emits writers | RED | draft carries no `writers:` key (KeyError in the roster comparison); verbatim copy keeps `benih:` and `agents: benih` |
| 3b writers parent drafts writers | GREEN guard | parsed roster equality held |

## Strings w1 must reword (from the measured reds)

- cli.py harvest `help=` one-liner: `tuai: close a season into akar (step 4)`
  — it renders in the top-level `--help` verb list.
- cli.py cmd_evolve_reject / cmd_evolve_rollback log strings:
  `musim/rejected/` must become the real seasons/rejected/ path and
  `akar record` must become `ledger record`.
- akar.py logger line `appended akar record %s -> %s` — it is stderr and
  in the band's sweep scope; one-word reword to `appended ledger record`.
  The module name stays (w1 scope correction says so).
- audit --last help: `audit the last N musim seasons` → `seasons`.
- evolve `_render`: rewrite `benih:` → `writers:` and `agents: benih` →
  `agents: writers` in drafts; roster/budgets byte-identical otherwise.
- Not pinned and not in w1's stated scope (residual, operator's call):
  engine `_validate_benih` error strings still say `benih '<name>'`.
  No pin blocks on them (my prompt named evolve reject/rollback as the
  stderr surfaces; the engine is read-side in w1's deliverable 1).

## Merge gates (measured)

- s45 rename pins green: **10 passed in 0.74s** on current main; the file
  was never written by this session (byte-identical by construction).
- Full-suite baseline on current main: PENDING (background run
  b2okw38tl; fills in below when it signals).
- At merge: the 5 red pins go green from w1's src changes; the only
  full-suite reds must be the two known race flakes.

## Verify protocol used

- ruff: `~/.local/bin/ruff check --no-respect-gitignore --line-length 100`
  → All checks passed.
- Interpreter: repo `.venv` python 3.13.12 with `PYTHONPATH=src`
  (probe: `python -m rumpun --version` → 0.11.0). The pins' subprocess
  helper re-derives src via the pyproject walk-up, so pre-graft and
  grafted runs behave identically.
- Full-suite log: /tmp/s54_w2_full.log (outside the repo).
