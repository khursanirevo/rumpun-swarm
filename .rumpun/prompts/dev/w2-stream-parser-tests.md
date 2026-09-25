# s16 w2 — spec-first tests for the stream tool-evidence parser

You are w2 in season s16 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13 and 15, src/rumpun/engine.py, akar records
stall-rule-fired-on-runtime and audit-4. Do NOT implement — w1 owns
engine.py. You own the test contract, spec-first: new tests FAIL against
current code, PASS once w1's patch lands. Use your FILE TOOLS (Write/Edit);
no nested-heredoc patch scripts.

## Deliverables (write ONLY inside your workspace; the harness merges)

1. tests/test_rumpun.py based on the current repo file (55 tests kept;
   additions + minimal helpers only — diff must be additions-only).
2. notes.md — what each test pins; the expected red set.

## Contract to pin (from the s16 season yaml)

1. `stream_tool_names(text)`-equivalent behavior via the engine's parser:
   line-delimited JSON, tool names from tool_use blocks, empty text ->
   empty set, malformed lines skipped (one DEBUG log each), U+2028 inside
   JSON strings is NOT a line break (split on "\n" only — w1/s15's rule).
2. file_tools lifecycle: true on first FILE_TOOLS event; ToolSearch/
   WebFetch/Task/Agent alone never set it; false only at finalize with
   >=1 parseable event and zero file-tool events; absent when the stream
   held zero parseable events.
3. Offset semantics: second scan over unchanged bytes re-classifies
   nothing (stream_offset in workspace state.json advances; additive).
4. Real-stream replay: truncated COPIES (first 200KB) of
   .rumpun/rimba/s15/w1/agent.log and w2/agent.log classify file_tools
   true for both (both carry Bash tool_use events early in the stream).
   Copy via shutil in-test from the repo tree; skip paths that don't
   exist (the fixture must not break fresh clones).
5. Additive-key safety: snaps with file_tools/stream_offset render
   byte-identical reports and identical audit F4 counts (reuse the
   toolless-mark test pattern).
6. No new polling: scanning happens in the existing watcher cycle.

## Constraints

- logging, never print; ruff check clean (line-length 100); py3.10+.
- Do not modify src/ or cli.py. tests + notes.md only.
- No real model output pasted into fixtures beyond the truncated stream
  copies; never any API keys or token values.
- ruff --no-respect-gitignore on your files (rimba/ is gitignored).

## Verify before finishing

Run your file against CURRENT code: expected red set in notes.md. The
harness re-runs the suite after merge; 55 green + new green is the gate.
