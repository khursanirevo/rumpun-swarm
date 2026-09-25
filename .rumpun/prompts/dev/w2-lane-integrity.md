# s22 w2 — M6/M7 lane integrity + pins for M1/M5/M6/M7

You are w2 in season s22 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/collab.py, akar record
codex-review-2026-09-14 (M6 + M7 with reproductions), and s21 evidence
(the repro-first pattern). You own collab.py + tests/; w1 owns
report/engine. FILE TOOLS directly. 40 minutes.
WRITE ONLY inside your workspace (the s21 writers broke that rule; do not).

## M6 — harness fields are authoritative

Today append_event expands the payload AFTER assigning seq/from, so
{"seq": 99, "from": "forged"} lands verbatim (reviewer reproduced). Fix:
assign harness fields after payload expansion, or reject payloads
carrying reserved keys (seq, from, ts) with a LaneError — pick one,
document it, pin it.

## M7 — readers never observe partial rows

Today readers hold no shared lock and large rows span multiple writes;
a crashed writer can also leave a partial tail that later appends
corrupt forever. Fix: readers take LOCK_SH on the lane lock for the
whole read; append takes LOCK_EX, writes the row in ONE os.write of the
serialized bytes to an append-mode fd, and recovers a detected partial
tail (last line not valid JSON + file lacks trailing newline) under the
exclusive lock before appending — log the recovered byte count, never
the content.

## Spec-first pins (red against current code)

- M6: forged seq/from rejected or overridden (per the chosen contract).
- M7: a reader thread under a barrier never parses a partial row while a
  writer appends large rows concurrently; a hand-crafted partial tail is
  recovered on the next append (byte count logged, subsequent reads clean).
- M1 (w1's patch): rendering a running season twice from unchanged
  persisted bytes is byte-identical; links sorted.
- M5 (w1's patch): a both-agents-fail season finalizes with an honest
  status and the verb maps it to nonzero.

## Constraints

- tests additions-only vs the current repo file (103 tests kept).
- collab.py patch as a workspace copy + notes.md anchors (harness merges).
- logging, never print; ruff clean (line-length 100); py3.10+.

## Verify before finishing

Measured red set against current code in notes.md; the 103 existing tests
green; your collab.py copy passing your M6/M7 tests in a scratch tree.
