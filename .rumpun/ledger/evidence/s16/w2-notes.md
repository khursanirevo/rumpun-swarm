# s16 w2 — notes: spec-first stream tool-evidence tests

Deliverable: `tests/test_rumpun.py` (workspace copy) — a pure addition to the
repo file. Diff against `tests/test_rumpun.py` at HEAD: 0 deleted lines,
385 added lines. The 55 existing tests are byte-identical and untouched.
15 new test items (13 functions; the replay test is parametrized over the
two s15 writers). They pin the s16 contract red against the current engine
and green once w1's engine patch lands.

## What each test pins

| test | pin |
|---|---|
| stream_tool_names_empty_text | empty text -> empty set |
| stream_tool_names_collects_names | tool names come from tool_use blocks only; a text block in the same event is ignored; raw names collected (Bash, WebFetch) before any FILE_TOOLS classification |
| stream_tool_names_skips_malformed_lines | exactly one DEBUG record per malformed line on the rumpun.engine logger; a blank line stays silent; parseable lines still classified |
| stream_tool_names_u2028 | a raw U+2028 inside a JSON string value is NOT a line break; lines split on "\n" only (a str.splitlines implementation fails this test) |
| scan_marks_file_tools_on_first_event | ToolSearch-then-Bash stream: one scan sets file_tools=true (sticky) and stream_offset at log end in workspace state.json |
| scan_toolsearch_class_never_marks | ToolSearch/WebFetch/Task/Agent-only stream: no file_tools key mid-stream (only finalize may set false), bytes still consumed (offset advanced) |
| finalize_false | >= 1 parseable event, zero file-tool events -> snap file_tools is False in the returned state and the persisted _season/state.json |
| finalize_absent | zero parseable events (empty log) -> file_tools key absent everywhere; never guessed |
| finalize_true | stream holding a file-tool event -> snap file_tools True |
| offset_additive | offset = old + appended; a parser spy proves only appended bytes go through the parser; a scan over unchanged bytes calls the parser zero times; true is sticky across later scans |
| real_stream_replay w1/w2 | first 200 KiB of each real s15 agent.log classifies file_tools true for both writers; shutil copy from the repo tree; skips on fresh clones without the logs |
| report_document_unchanged | snaps/spawned carrying file_tools + stream_offset render byte-identical reports; determinism holds (s14 toolless-mark pattern) |
| audit_f4_unchanged | the same stamps leave run_audit's "route glm:" F4 line identical across two runs |
| watch_cycle_scans | full in-process start_season run reaches completed with snap file_tools true, workspace stream_offset > 0, and the scan invoked from the existing loop (no new polling) |

## Expected red set (measured against current code, run 2)

12 FAILED — the parser and scan do not exist yet (AttributeError on
`stream_tool_names` / `_scan_agent_stream` / `_parse_stream_events`), and
finalize writes no file_tools key:

- test_stream_tool_names_empty_text_yields_no_tools
- test_stream_tool_names_collects_names_and_ignores_other_blocks
- test_stream_tool_names_skips_malformed_lines_with_one_debug_each
- test_stream_tool_names_u2028_inside_json_is_not_a_line_break
- test_scan_agent_stream_marks_file_tools_on_first_file_tool_event
- test_scan_agent_stream_toolsearch_class_never_marks
- test_finalize_sets_file_tools_false_after_parseable_non_file_stream
- test_finalize_marks_file_tools_true_when_stream_had_a_file_tool_event
- test_scan_agent_stream_offset_additive_and_no_reclassification
- test_real_stream_replay_marks_writer_file_tools[w1]
- test_real_stream_replay_marks_writer_file_tools[w2]
- test_watch_cycle_scans_stream_and_finalizes_marks

3 new tests are already green now and stay green (regression guards):
finalize_absent (vacuously true today), report_document_unchanged, and
audit_f4_unchanged — `report._document` and the audit whitelist their
fields, so the additive keys are ignored by current code too.
All 55 existing tests pass in run 2. Post-merge gate expectation:
70 items green (the 2 replay items skip only in fresh clones).

## Judgment calls the merge reviewer should see

1. Truncation size is 200 * 1024 (200 KiB), not 200_000. Measured byte
   offsets of the first `"type":"tool_use"` event: w1 202605, w2 196577.
   Both writers carry exactly 2 Bash tool_use events within 200 KiB; a
   200_000-byte cut holds no file-tool event for w1 at all, which would
   make the s16 band ("both writers true") unreachable. The constant's
   comment records the numbers.
2. The scan is invoked through `_stream_scan`, which dispatches on
   `inspect.signature`: the w1 prompt writes `_scan_agent_stream(ws, meta)`,
   the s15 salvage block writes `_scan_agent_stream(root, sid, ws)`. The
   pinned contract is behavior (state.json gains stream_offset /
   file_tools), not the private signature, so either shape runs. A third
   shape fails loudly and is negotiable.
3. Finalize semantics are pinned through `engine._finalize` (stable,
   existing signature), asserting both the returned state and the persisted
   season state.json — the surfaces the report and audit read.
4. The replay fixture resolves the repo tree by walking up to the nearest
   ancestor holding `.rumpun` (correct at the merged tests/ location and
   from workspace copies), then `shutil.copyfile` + truncate; missing logs
   skip, so fresh clones never break.

## Watch item (pre-existing, not introduced by this diff)

`test_dual_start_single_spawner` failed once (run 1) under concurrent load
(s16/w1 was actively working in this repo): starter 2 acquired
_season/state.lock only after starter 1 had already finalized the
instant-exit season, so it hit the "already finished" reattach guard. It
passed on rerun (run 2, 58 passed including dual-start). This is a
load-sensitive race in the existing test's premise; this diff does not
touch it.

## Verification transcript

- Run 1 (pre-fix): 11 failed, 57 passed, 2 skipped in 2.74s — the replay
  pair skipped because the then-relative fixture path only resolves at the
  merged location; led to the `_repo_root()` walk-up fix.
- Run 2 (final): 12 failed, 58 passed, 0 skipped in 2.55s — the red set
  above, 55/55 existing green.
- `ruff check --no-respect-gitignore tests/test_rumpun.py`: All checks
  passed (line-length 100, py310, repo rule set E,F,I,UP,B,SIM,RUF).
- Diff vs repo `tests/test_rumpun.py`: 0 deleted, 385 added (additions-only).
