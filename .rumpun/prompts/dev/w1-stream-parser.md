# s16 w1 — engine stream parser + tool-evidence marks

You are w1 in season s16 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13 and 15, src/rumpun/engine.py, and akar records
stall-rule-fired-on-runtime, agentlog-no-tool-evidence, audit-4, s15-harvest.
You have FILE TOOLS — use Write/Edit directly; do NOT build nested-heredoc
patch scripts (that failure mode killed s15/w1's work: three corrupted
drafts in a row, in its own stream).

## Deliverables (write ONLY inside your workspace; the harness merges)

1. engine.py patch, applied by you to a COPY in this workspace
   (cp ../../../../../src/rumpun/engine.py ./engine.py then edit it), plus
   notes.md listing each anchor and what changed.
2. notes.md — design decisions + verification transcript summary.

## What to build (salvage basis exists)

The clean parser block w1/s15 authored is in
.rumpun/akar/evidence/s15/w1-commands-dump.txt command [24] (fixes from
[26] noted in the same file): _parse_stream_events, _tool_names,
FILE_TOOLS frozenset. Start from it; finish the integration:

- `_scan_agent_stream(ws, meta)`: read agent.log from meta's byte offset
  (additive key stream_offset in the workspace state.json), parse appended
  bytes, update meta: any tool name in FILE_TOOLS -> file_tools=true (once,
  never unset); write state back under the existing flock discipline.
- Watch loop: one _scan per live agent per existing cycle (no new polling;
  skip agents whose stream_offset equals the current log size).
- Finalize: for each agent, if file_tools unset and >= 1 parseable event
  existed in the whole stream -> file_tools=false; zero parseable events ->
  key stays absent (never guessed).
- ToolSearch/WebFetch/Task/Agent-class names NEVER count as file tools.
- Additive keys only; report.py/audit.py output bytes must not change.
- Never log stream content or token values: tool names, event counts,
  byte counts, paths only. logging, never print. ruff clean, py3.10+.

## Verify before finishing

Scratch-copy: apply your engine.py, replay BOTH real streams
(.rumpun/rimba/s15/w1/agent.log and ../w2/agent.log — 6.3MB/6.8MB) through
_scan (fresh offsets), report per-writer: file_tools verdict + tool names
found (expect Bash in both; expect true, true). Run the suite
(uv run pytest) — 55 tests must stay green. Put both results in notes.md.
