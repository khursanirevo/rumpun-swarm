# s15 w2 — spec-first tests for the stream tool-evidence classifier

You are w2 in season s15 of the rumpun campaign (repo root: the parent of
this .rumpun tree). Read DESIGN.md sections 13 and 15, src/rumpun/engine.py,
and akar records agentlog-no-tool-evidence and audit-3. Do NOT implement —
w1 owns engine.py. You own the test contract, spec-first: new tests FAIL
against current code, PASS once w1's patch lands.

## Deliverables (write ONLY inside your workspace; the harness merges)

1. tests/test_rumpun.py based on the current repo file (54 tests kept;
   insertions plus minimal helpers only — diff must be additions-only).
2. notes.md — what each test pins; run evidence (expected red set).

## Contract to pin (from the s15 season yaml + akar records)

1. `stream_tool_names(text: str) -> set[str]` in rumpun.engine: parses
   line-delimited JSON, returns tool names from tool_use blocks; empty
   text -> empty set; malformed lines skipped; a tool name inside nested
   content arrays is found.
2. File-tool detection: Write/Bash/etc -> snap["file_tools"] = true;
   ToolSearch or WebFetch alone NEVER set true (the s14 lesson: w1's
   tool-less log carried ToolSearch-class activity); non-file tool_use
   events leave the key absent until finalize decides false.
3. Finalize rule: >= 1 parseable event, no file tool -> false at finalize;
   zero parseable events -> key absent (never guessed).
4. Incremental parse: only appended bytes parsed between cycles (offset
   semantics — a second cycle over unchanged bytes re-classifies nothing;
   the additive stream_offset key carries the position).
5. Additive-key safety: snaps carrying file_tools/stream_offset render
   byte-identical reports (reuse the toolless-mark test pattern) and
   audit F4 counts unchanged; malformed stream lines never crash the
   watcher.
6. No new polling: classification happens in the existing watcher cycle.

## Constraints

- logging, never print; ruff check clean (line-length 100); py3.10+.
- Do not modify src/ or cli.py. tests + notes.md only.
- Never include API keys or token values; synthetic streams only — no
  real model output pasted into fixtures.
- ruff --no-respect-gitignore on your files (rimba/ is gitignored).

## Verification before you finish

Run your file against CURRENT code: state the expected red set in
notes.md. The harness re-runs the suite after merge; 54 green + new green
is the s15 gate.
