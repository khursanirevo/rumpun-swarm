# s16 w1 — engine stream parser + tool-evidence marks

Deliverables: `engine.py` (patched copy, 583 lines) and this notes.md.
Status: done. Both real streams replay green, suite 55/55, ruff clean.

## Anchors (engine.py, original 362 lines)

| Anchor | Change |
|---|---|
| module docstring | +9 lines: stream-evidence contract paragraph |
| after `class EngineError` | +198 lines: FILE_TOOLS, _parse_stream_events, _tool_names, stream_tool_names, _write_agent_state, _root_sid, _mark_file_tools, _scan_agent_stream, _finalize_agent_stream |
| watch loop | +12 lines: one _scan per live agent per existing cycle; meta read fresh from ws/state.json; terminal agents classify at finalize only |
| `_finalize` | +2 lines: _finalize_agent_stream for each spawned agent |

## Salvage basis

Block from akar/evidence/s15/w1-commands-dump.txt command [24]; the three
[26] fixes applied: `encoding="~utf-8"` → `utf-8`; `events +=  records... +1`
→ `events += 1`; `_write_agent_state(meta=meta, ws=ws)` →
`_write_agent_state(ws, meta)`. Everything else in [24] landed verbatim.

## Design decisions

- Marks live only in the workspace state.json (`stream_offset`, `file_tools`).
  `_agent_snap` output is untouched, so snaps carry no new keys and
  report.py/audit.py output bytes cannot change. A/B finalize byte-compare
  backs this (see transcript).
- `_scan_agent_stream(ws, meta)` keeps the brief's signature. It derives the
  season lock from ws (`_root_sid`: ws.parents[2], ws.parent.name) and holds
  the `_season/state.lock` flock only around the state write. Helpers own
  their locking; both docstrings carry the no-nesting hazard (flock is per
  open fd; a second fd blocks on itself).
- Concurrent-scan convergence: two scans starting from equal offsets parse
  equal bytes, so lost-update windows cannot lose a mark; the flock
  serializes the file writes themselves.
- Sticky `file_tools=true` freezes `stream_offset` at the first file-tool
  sighting: after the mark there is nothing left to record, so scanning
  stops. Finalize advances the offset to EOF only on its true/false writes.
- `FILE_TOOLS` is a positive set. ToolSearch, WebFetch, Task, and Agent-class
  names are absent from it, so they can never count. No keyword matching
  anywhere — the w4 fixture pins this.
- `file_tools=false` requires >= 1 parseable event; zero parseable events
  leaves the key absent. A tool-less glm text log classifies absent, not
  false — the engine never guesses.
- Divergence from s15's draft patch spec ([27]): s15 scanned every spawned
  agent under a caller-held lock and re-read state.json inside the scan.
  This landing scans live agents only, per the s16 brief, and passes meta
  in.
- Log discipline: WARNING carries path + tool name; DEBUG carries byte
  counts; nothing logs stream content or token values.

## Verification transcript

✅ VERIFIED REAL — all runs below executed this session.

- Suite: `uv run pytest -q` → 55 passed. Run twice (session start and
  close); repo untouched all session.
- Replay: `uv run python .rumpun/rimba/s16/w1/replay.py`, patched module
  loaded by explicit path (logged `__file__` proves the workspace copy ran).
  Real streams copied to scratch with fresh offsets.

| Fixture | Scan verdict | Offset vs size | Parseable events | Tool names |
|---|---|---|---|---|
| s15 w1 (6,316,289 B) | true | equal | 30,680 | Bash |
| s15 w2 (6,766,350 B) | true | equal | 32,689 | Bash |
| w3 text-only | absent | equal (12) | 0 | none |
| w4 ToolSearch-only | false at finalize | equal (163) | 2 | ToolSearch |
| w5 truncated→completed, 2 scans | true | 2,619 then equal (6,316,289) | n/a | Bash |

- Independent cross-check: `grep '^{' | jq` census over the real streams:
  w1 29 Bash, w2 17 Bash; 30,680 and 32,689 JSON lines. Counts agree with
  the engine parser line for line. The 29/17 also match s16.yaml.
- Incremental: scan 1 on a 4,096-byte truncated copy consumed 2,619 bytes
  (partial trailing line held back); scan 2 after appending the rest reached
  EOF and marked true.
- A/B finalize: identical synthetic season finalized by the base repo engine
  and by the patched engine. Season state and read_status content identical;
  the only delta was `ended_at` wall-clock. Additive-key safety also holds by
  the existing suite tests (report bytes, audit F4 counts).
- `ruff check --no-respect-gitignore .rumpun/rimba/s16/w1/engine.py` → clean;
  `py_compile` OK. The flag matters: rimba/ is gitignored, so a plain
  directory run checks zero files.

## Limitations

- The lane-event branch of `_mark_file_tools` (collab groups) never executed
  in the replay; replay fixtures carry no `collab` key. prepare_lane/
  append_event signatures were checked against collab.py; w2's spec-first
  tests can pin that path.
- Scratch log copies were removed after the run; replay.py and
  replay-results.json stay in the workspace as the transcript evidence.
