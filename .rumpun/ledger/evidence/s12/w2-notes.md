# notes — w2 README sync (s12)

Sources read (all at HEAD fb93658): `README.md`, `src/rumpun/scaffold.py`,
`src/rumpun/cli.py`, `src/rumpun/engine.py`, `src/rumpun/evolve.py`,
`src/rumpun/report.py`, `src/rumpun/routes.py`, `src/rumpun/lint.py`,
`src/rumpun/harvest.py`, DESIGN.md (s10-s12 sections, dashboard notes),
`.rumpun/akar/2026-09-14_audit-1.md`, `.rumpun/akar/2026-09-14_s11-harvest.md`.

## Command re-verification, verb by verb

| README command | Evidence in cli.py / module | Verdict |
|---|---|---|
| `rumpun init [TARGET]` | `cmd_init` -> `scaffold.init_project`; target defaults to `.` | match; scaffold list fixed (see Fixes) |
| `rumpun models --write` / `--probe` | `cmd_models`; `routes.write_routes` fills `routes: {}`; `--probe` runs one completion per claude route | match |
| route keys `glm`, `claude`, `gpt-5.6-sol` | `routes.proxy_family` (z.ai -> glm), login family `claude`, codex slugs from `~/.codex/models_cache.json` | match |
| seeded `glm-5.2`/`fable` placeholders | `scaffold.MUSIM_S1` benih routes | match |
| `rumpun lint <file>` | `cmd_lint` -> `lint.lint`: required keys, DAG, artifact contracts, prompt existence, citation resolution; `_lint_preflight` gates `season start` | match |
| `rumpun graph <file>` | `cmd_graph` -> `graph.mermaid` | match |
| `rumpun direct TEXT` / `--list` | `cmd_direct`: appends pending to `akar/directives.jsonl`; list prints pending first | claim fixed (see Fixes) |
| `rumpun season start <file>` | `cmd_season_start`; engine spawns one-shot children in own process groups, blocks on stop rules; requires `routes` filled first | match |
| `rumpun season stop <id>` | `cmd_season_stop` -> `engine.stop_season` (stop-flag + finalize) | match |
| `rumpun board <id>` | `p_board` -> `cmd_season_status`; board parser takes no `--json` | match (the "--json only on season status" line is correct) |
| `rumpun season status <id> [--json]` | `cmd_season_status` -> `engine.read_status` | match |
| `rumpun season show <id> [--json]` | `cmd_season_show`: status line, `_deliverables`, `_lanes` counts | match |
| `rumpun season list` | `cmd_season_list`: id, status, duration, agent count; `no state` when state.json absent | match |
| `rumpun season report <id>` | `report.render_report` -> `rimba/<sid>/report.html` | match |
| `rumpun season report <id> --serve` | `_serve_rimba`: 127.0.0.1:8611, prints `localhost:8611/<sid>/report.html`, KeyboardInterrupt exits 0 | match |
| `rumpun harvest <id> --verdict --implies` | `cmd_harvest` -> `harvest.harvest_season`; verdict choices WIN/LOSS/NEUTRAL/INVALID; one akar record | match |
| `rumpun audit [--last N]` | `cmd_audit` -> `audit.run_audit`; default `--last 10` | added (see Fixes) |
| `rumpun evolve plan <parent>` | `evolve.draft_next`: drafts s<N+1>, parent must be latest, empty `primary_change` skeleton | match |
| `rumpun evolve apply <draft>` | `evolve.apply`: lint gate; empty skeleton fields are lint errors | match |
| `rumpun evolve approve <draft>` | `evolve.approve_draft`: akar record only, draft unmodified | match |
| `rumpun evolve reject <draft>` | `evolve.reject_draft`: moves to `musim/rejected/`, P33 record | match |
| `rumpun evolve rollback <id>` | `evolve.rollback_season`: moves season YAML, records containment, never runs git | match |

Version pins unchanged: `pyproject.toml` requires-python `>=3.10`, version
0.10.0; the README keeps "Python 3.10 or newer" and `uv pip install -e .`.

## Fixes beyond the lifecycle rewrite

1. Season lifecycle opens with the lean default: two phases, execute (the
   benih build the step) and evaluate (the judge writes verdicts); why line:
   reflection (s11's audit) found the longer declared pipeline unexercised;
   extra phases can be declared per-season when a task needs them.
   Evidence: `akar/2026-09-14_audit-1.md` — analyze, rank_gaps, hypothesize,
   plan, falsify wrote their artifacts in 0 of 8 engine seasons; execute and
   evaluate in 7 of 8. DESIGN.md s12: "the declared pipeline trims to
   execute -> evaluate ... the only lint-clean trim."
2. `rumpun init` scaffold list: added `README.md` — `scaffold.init_project`
   writes `.rumpun/README.md`; the old list omitted it.
3. `rumpun direct`: dropped "Directives are consumed at the next phase
   boundary". No consumer exists in src: `grep -rn directive src/rumpun/`
   hits only the CLI append/list paths and a prompt string. The jsonl schema
   keeps `status` for a future consumer; the README now states only the
   implemented behavior (append, list pending first, no injection into a
   running agent).
4. Added the `rumpun audit [--last N]` block to the Evolution loop. It ships
   at v0.10.0 (commit fb93658) and is listed in cli.py's docstring, but the
   README predates it. Judgment call: this documents an existing verb, not a
   new one, and the lifecycle why-line names s11's audit, so the verb had to
   be reachable from the README.
5. `akar/` table row: now names harvest, audit, approval, and rollback
   records; it said only "harvest records and findings".

## Phase naming sweep

The old README never enumerated the seven phases, so the rewrite touched
three spots only: the new lifecycle opening (the two phases), the audit
block (references the lean default), and nothing else. The `prompts/` table
row stays generic ("phase prompt templates") — it matches both the current
`prompts/base/` contents and the post-trim pair.

## Lane protocol (v2) compliance

`lane_tool.py` ported from s11/w2 (protocol v2: events are evidence, never
gates). Posted kind=start (seq 0), kind=policy (seq 1), kind=done after
verification. No waits on w1.

## Checks run

- `ruff check .rumpun/rimba/s12/w2/lane_tool.py` — passed (repo config:
  line-length 100, select E,F,I,UP,B,SIM,RUF).
- Full readback of all three written files (memory: verify state writes).
- Lane event readback after each post.

Not run: `rumpun lint`/e2e against the rewritten README — it is a document;
no code paths consume it. The repo README itself was not modified; the
deliverable lives in this workspace only.
