# s36 w2 notes — spec-first pins for the stall-resume drafting logic

Deliverable: `tests/test_rumpun.py` (this workspace's copy) = the repo tests
file (5347 lines, untouched) + one appended 173-line s36 section with 4 pins.
Merge = append only. All evidence under `scratch/evidence/`.

## Measured red set vs the pre-s36 tree (repo HEAD 3606c8b; src/ untouched by w2)

| # | pin | measured status | measured reason |
|---|---|---|---|
| 1 | `test_draft_from_stopped_stall_parent_resumes_budgets_and_cites_stall` | RED | `{'alpha': 15, 'beta': 40} != {'alpha': 23, 'beta': 60}`; no header comment names `stopped_stall` |
| 2 | `test_draft_from_stopped_stall_parent_budget_25_rounds_to_38` | RED | `{'w1': 25} != {'w1': 38}` |
| 3 | `test_draft_completed_parent_byte_identical_to_pre_s36` | GREEN (guard) | golden == today's live output (byte-identity held) |
| 4 | `test_draft_no_state_parent_byte_identical_to_pre_s36` | GREEN (guard) | same golden, no-rimba-state fixture |

The two red pins fail for the intended spec reason (assert lines captured in
`pins-run.txt`). Pins 3-4 are green-guard by nature: they pin today's bytes
(the golden) and must stay green after w1's patch lands.

## Contract pinned (musim/s36.yaml expected_band + the w1 brief; akar audit-25)

- draft_next reads the parent's persisted engine state
  (engine.read_persisted_status on the parent sid) and branches on terminal
  status;
- stopped_stall parent: every benih budget = parent x 1.5, rounded UP
  (ceil); the yaml header gains a stall citation comment naming the parent's
  status and sid;
- non-stall parents (completed status, or no persisted state at all):
  byte-identical to today -- no budget change, no citation header.
- Rounding: 25 -> 38 (ceil(37.5)); pin 1's 15-minute benih discriminates
  ceil from round-half-even (ceil(22.5)=23 vs round(22.5)=22).

## Evidence

- `pins-run.txt`: 2 failed, 2 passed, 171 deselected (workspace copy, venv
  pytest; the two reds fail at the budget asserts quoted above).
- `suite-run.txt`: repo tests file at the repo: 171 passed in 62.13s,
  exit 0 (background run, read from the log's exit line).
- `ruff-run.txt`: ruff 0.14.10, `--no-respect-gitignore`, line-length 100
  via the repo pyproject: All checks passed (exit 0).
- Collection: 175 tests collected from the merged file (171 + 4).
- Golden: `scratch/evidence/golden_draft_s36.txt` + `.provenance.json`
  (git HEAD, evolve.py sha256, golden sha256), captured by
  `scratch/capture_golden.py` (tmp+replace, full readback). The literal was
  built from that file programmatically; the A/B pins' green run is the
  byte-level proof the embedding matches live output.

## Build integrity (the known write-corruption pattern, self-caught)

Two staging-file Writes corrupted mid-parameter (leaked drafting meta-text,
mangled literals, one syntax error); discarded before any append. One
parallel-Write batch bled parameters across sibling calls and misrouted one
file outside the workspace (removed). Recovery: small sequential part files
with per-part readback, golden literal built by script from the capture
(no transcription), atomic append gated by head-cmp against the repo file;
`py_compile` passes. The first builder run had a `splitlines()` vs
`splitlines(keepends=True)` bug that collapsed the golden literal to one
newline-free string -- caught by the A/B pins themselves on the first pin
run, fixed, rebuilt on a pristine copy, re-verified.
