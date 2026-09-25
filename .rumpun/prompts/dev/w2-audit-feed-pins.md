# s76 w2 — pins for the audit-to-board feed (seq 14 discipline)

w1 files audit candidates as issues and closes issue #1 via sync. Your
slice: pin the feed's offline-verifiable contract so the loop is held
by tests, not hope.

## Ground truth
- audit records carry `candidate: ` lines (the kanban backlog reads
  them the same way — the s66 convention)
- board.py: issue_create_argv(title, body), item_add_argv(number, url),
  sync_season, issue_for_season (map first, lane-title match second)
- the s75 board landed: project 1, issue #1

## Task (spec-first, pins in tests/test_s76_w2_pins.py, _s76w2_ prefix)
1. board.py grows: candidates_from_audit(record_path) — the verbatim
   candidate lines of an audit record (pure read, pinned on a fixture
   record file).
2. board.py grows: audit_issue_argv(candidate, citation) — the exact
   argv filing one candidate as an issue (title compressed to <=60
   chars deterministically, body = candidate + citation), pinned
   argv-exact on a fixture candidate.
3. Pin sync_season --dry-run against a fixture campaign + fixture
   pickup rows: the render names the issue, the comment body carries
   the sealed record text, and nothing is written.
4. Pin the real --sync outcome shape only via the record/exit contract
   (no live gh call in pins; w1's notes.md is the live evidence).

## Bounds
- Edits: src/rumpun/board.py, tests/. notes.md REQUIRED. No .rumpun
  state edits; no real gh call in pins.
