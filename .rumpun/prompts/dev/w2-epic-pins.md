# s58 w2 — spec-first pins for the epic rollup

You are w2 in season s58 (repo root: the parent of .rumpun). Read
src/rumpun/cli.py, src/rumpun/lint.py, src/rumpun/engine.py, ledger
records s56-harvest + audit-40, and ledger directives seq 5; the s56 pins
(tests/test_s56_w2_pins.py) are the shape precedent. You own tests/;
w1 owns cli.py + lint.py. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Spec-first pins (red against current code)

1. `rumpun epics` with a declared two-epic fixture renders one line per
   epic: id, season span (min-max member ids), the verdict rollup
   (X WIN / Y LOSS / Z other from runs state + harvest verdicts), and
   the epic title (subprocess, 120s bound).
2. Duplicate membership: the same season id in two epics lint-errors
   naming the season and both epics; an epic member with no season yaml
   lint-errors too.
3. Missing-state honesty: a member with no run state renders "no state"
   in its line, never a fabricated verdict; no epics.yaml renders the
   flat hint and exits 0.
4. Immutability: running the verb (and epics --init) leaves the ledger
   directory byte-identical (hash before/after in the pin).

## Constraints
- tests/ additions-only; subprocess pins, timeout bounded (120s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ - w1 owns cli.py + lint.py; the harness merges.

## Verify before finishing
Measured red set in notes.md; all pins green at merge; the suite floor
holds.
