# s25 w2 — fixes or honest drift for every matrix break + pins

You are w2 in season s25 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, akar record audit-13, and the runner + matrix
w1 is building in the shared lane (lane events: the matrix lands as
replay-matrix.md). You own src/ and tests/ fixes for anything the matrix
proves REGRESSED on main. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Deliverables

1. For each matrix REGRESSION: fix the code on main (the repro scripts
   encode ratified behavior from s17-s24; main drifted through merge
   reconciliations, so main is usually the side to fix) - patched copies
   in your workspace + notes.md anchors, harness merges.
2. For each matrix DRIFT (the script's assumptions aged, main is right):
   record the drift in notes.md with the exact delta; do NOT change main
   to match an aged script.
3. A regression pin: the runner's matrix (or its all-green summary) is
   executable evidence - add one test that runs the runner and asserts
   no REGRESSION verdicts (skips allowed for scripts w1 marks SKIP).

## Rules

- A regression fix must keep the 123-test suite green (run it).
- Never edit the historical scripts' meaning; adaptation lives in the
  runner (w1's file).
- logging, never print; ruff clean (line-length 100); py3.10+.

## Verify before finishing

Re-run the runner against your patched copies: no REGRESSION verdicts
remain (DRIFT records are acceptable and honest). Suite green. Both in
notes.md.
