# s15 w1 — engine stream-json tool-evidence classifier

You are w1 in season s15 of the rumpun campaign (repo root: the parent of
this .rumpun tree). Read DESIGN.md sections 13 and 15, src/rumpun/engine.py
(spawn + watcher + finalize path), and akar records agentlog-no-tool-evidence
and audit-3. Background: s14 falsified text-log classification (marker+size
rule tp=7 fn=1 fp=21 tn=2 over 31 logs). The deterministic signal is the
spawn's own structured stream: the new fable route runs
`claude -p --output-format stream-json --verbose`, so agent.log now holds one
JSON event per line (system/assistant/user/result types; tool calls appear
as tool_use blocks with a tool name inside assistant message content).

## Deliverables (write ONLY inside your workspace; the harness merges)

1. engine.py patch (targeted diffs in notes.md + the patched functions).
2. notes.md — design decisions, verification runs.

## Classifier contract (pin this shape)

- Pure function `stream_tool_names(text: str) -> set[str]`: parse each line
  as JSON (json.loads), collect every tool name from tool_use blocks
  (assistant message content arrays). Malformed lines: skip silently from
  classification, log one DEBUG per occurrence. Empty text: empty set.
- Engine tracks a per-snap byte offset (additive snap key `stream_offset`)
  and parses only appended bytes each watcher cycle — no full re-reads, no
  new polling (existing cadence only).
- On the first parsed file-tool name (set: Read, Write, Edit, Bash, Grep,
  Glob, NotebookEdit, WebFetch is NOT a file tool, ToolSearch is NOT):
  snap["file_tools"] = true, one WARNING with path + tool name only, one
  collab lane event. Never re-evaluated once true.
- At finalize: if the stream held >= 1 parseable event but no file-tool
  name ever appeared, snap["file_tools"] = false. Fewer than 1 event: key
  stays absent (never guessed from absence of a stream).
- Additive keys only (file_tools, stream_offset); never rewrite existing
  keys; report.py and audit.py must keep byte-identical output (suite
  proves it).
- Never log stream CONTENT or token values — event types, tool names,
  byte counts only.

## Constraints

- logging, never print; ruff check clean (line-length 100); py3.10+.
- Do not touch cli.py, audit.py, report.py, tests/, or the route table —
  w2 owns the test contract; the harness merges.
- stdlib only.

## Verification before you finish

Scratch-copy the repo, apply your patch, drop a synthetic stream into a
fake workspace, run the watcher once, show the snap state, and run the
suite (uv run pytest). Put the transcript summary in notes.md. State what
is measured vs expected — no projected numbers presented as measured.
