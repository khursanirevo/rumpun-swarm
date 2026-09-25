# s22 w2 — M6/M7 lane integrity + M1/M5 pins

## Measured results

- Red set against base HEAD 94fc731 (scratch/base = `git archive HEAD` + this
  workspace's tests file; base src forced via PYTHONPATH): **5 failed, 101
  passed, 2 skipped** — all five pins red. Captured: `scratch/red-base.txt`.
  The two skips are the s16 real-stream tests (fixtures untracked, absent
  from git archive; they pass in the repo tree — repo suite: 103 passed in
  32.30s, captured `scratch/suite-repo.txt`).
- Green tree (scratch/green = base + this workspace's collab.py + tests):
  **2 failed, 104 passed, 2 skipped** — the two failures are exactly the M1
  and M5 pins (w1's patches, spec-first for that lane). My three lane pins
  are green there. Captured: `scratch/suite-green.txt`.
- Lane pins stability: 3 consecutive runs, 3 passed each, 0.49s per run
  (`scratch/lane-pins-green.txt`).
- Ruff clean (line-length 100, `--no-respect-gitignore`): `scratch/ruff.txt`.
- Additions-only proof: `diff` of workspace tests/test_rumpun.py vs the repo
  file shows 0 deleted lines; the 103 existing tests are kept.

## Contract decisions

- **M6: REJECT** (documented in the collab.py module and append_event
  docstrings). A payload carrying a reserved key (seq, from, ts) raises
  LaneError before the lock; nothing is written. Harness fields are also
  assigned after payload expansion (`event = {**payload, "seq": seq,
  "from": sender}`) as defense in depth. The pin rejects all four forged
  shapes, checks the lane stays empty, and checks a clean append keeps its
  harness-assigned seq/from.
- **M7**: read_events holds LOCK_SH on the lane lock for the whole read;
  append_event holds LOCK_EX, recovers the tail before counting, then writes
  the row as ONE `os.write` of the serialized bytes to an O_APPEND fd with a
  full-write check (a short write raises LaneError — no silent partial).
  Recovery condition is exactly the review's: file lacks a trailing newline
  AND the last line is not valid JSON; truncated under the held lock;
  `logger.warning("%s: recovered %d bytes of partial tail", ...)` — byte
  count only, never content.
- Known boundary, documented rather than widened: a tail that lacks a
  newline but IS valid JSON is left in place per the review's condition, so
  the next append glues onto it. Out of scope this season; backlog item.

## M7a pin design note (measured, not assumed)

The review's literal shape (reader racing append_event's large rows) stayed
base-green under 12×512KB and 40×1MB pressure: CPython's BufferedWriter
pushes a large row out at close as one bulk write, so the reader rarely has
a mid-row window. The pin instead holds LOCK_EX from the test, places a
partial row's bytes, then barrier-releases the reader: base readers parse
the partial tail deterministically (LaneError inside the 0.3s window);
patched readers block on LOCK_SH, and the pin asserts blocked-then-clean.
Structural, not scheduler luck. Lesson saved to my memory
(buffered-write-race-pins).

## Anchors

- Review: `.rumpun/akar/2026-09-14_codex-review-2026-09-14.md` (M1, M5, M6,
  M7); reproductions in
  `akar/evidence/codex-review-2026-09-14/review-full.txt:6585-6597`.
- Merge targets: workspace `collab.py` → `src/rumpun/collab.py` (75 lines →
  148); workspace `tests/test_rumpun.py` → `tests/test_rumpun.py`
  (additions-only).
- tests/test_rumpun.py (workspace copy): RUMPUN_YAML_FAIL :2577; M6 pin
  :2586; M7a pin :2602; M7b pin :2646; M1 pin :2677; M5 pin :2726.
- M5 contract for w1: the honest status value is `"failed"` (from the
  engine's TERMINAL vocabulary) and `season start` returns nonzero. M1
  contract for w1: byte-identical renders from unchanged persisted bytes
  and sorted workspace links; the pin renders twice 0.35s apart.
- Captured outputs: `scratch/red-base.txt`, `scratch/suite-green.txt`,
  `scratch/lane-pins-green.txt`, `scratch/suite-repo.txt`,
  `scratch/ruff.txt`. Trees: `scratch/base` (HEAD + my tests),
  `scratch/green` (HEAD + my collab.py + my tests).
