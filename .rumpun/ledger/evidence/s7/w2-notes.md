# w2 notes — README sync for the v0.7.0 surface

Base: repo README.md and src/rumpun/cli.py at commit efc4c8f (code version
0.6.0; README documents the v0.7.0 surface). Every quickstart command was
re-checked against the cli.py verb/flag surface; findings below.

## Re-verified, unchanged

- `rumpun init` — verb exists, `target` optional, defaults to `.`
  (cli.py `build_parser`).
- `rumpun lint <file>` — exists; error-severity findings block
  `season start` via `_lint_preflight` (P27).
- `rumpun graph <file>` — exists, prints mermaid.
- `rumpun season start <file>` — exists; `season stop` from another terminal
  is real (`cmd_season_stop`).
- `rumpun board s1` — dispatches to `cmd_season_status`; `board` and
  `season status` both carry `--json`. Paragraph as written is correct.
- `rumpun season list` — `cmd_season_list` prints `no state` when the season
  state is absent; wording correct.
- `rumpun season report s1` — render target is `.rumpun/rimba/s1/report.html`
  (`report_mod.render_report` default). `--serve` binds 127.0.0.1:8611,
  prints the `s1/report.html` URL, Ctrl-C exits 0; SimpleHTTPRequestHandler
  serves GET/HEAD only, so "read-only" holds.
- `rumpun harvest s1 --verdict WIN --implies "..."` — `--verdict` choices
  WIN/LOSS/NEUTRAL/INVALID, `--implies` required; example uses a legal pair.
- `rumpun evolve plan` — skeleton fields `baseline`, `expected_band`,
  `rollback`, `eval_window` match `_PRIMARY_CHANGE_SKELETON` (evolve.py);
  `evidence:` resets to `[]`, so "add akar citations under evidence:" holds.
- `rumpun evolve apply` — runs the lint gate; empty skeleton fields are lint
  errors, so apply fails while unfilled (evolve.py `apply`).
- Scaffold list in the `init` paragraph matches `scaffold.init_project`
  (rumpun.yaml, musim/s1.yaml, musim/_template.yaml, prompts/base/, akar/,
  rimba/).

## Drift found and fixed

- `season show` was listed under "Not implemented yet" with `--prompt` and
  `--events` flags. It is implemented since v0.6.0 (`cmd_season_show`):
  status line, per-agent deliverable files (engine bookkeeping excluded),
  lane event counts. Its only flag is `--json`. Removed the stub row; added
  the quickstart entry after `board` with `--json` only.
- `models --probe` description said "one small completion per route"; the
  code probes claude routes only (`cmd_models`). Fixed to "per claude route",
  matching the parser help text.

## Added per task (not yet in cli.py)

- `rumpun direct "one line of operator intent"` and `rumpun direct --list`:
  top-level verb per task and DESIGN.md P8 (appends to
  `akar/directives.jsonl`, consumed at the next phase boundary, never
  injected into a running agent). Current cli.py still carries the old
  `season direct` stub in `SEASON_STUBS`; `direct` lands in v0.7.0. This is
  the one README command that is not runnable on installed v0.6.0.

## Not-implemented table

- Now lists exactly `evolve approve`, `evolve reject`, `evolve rollback` —
  matches `EVOLVE_STUBS`. Stubs log a notice and exit 2, so the intro
  sentence still holds.

## Version pins

- README contains no version numbers; repo `__version__` is 0.6.0
  (src/rumpun/__init__.py), pyproject 0.6.0. Nothing older than v0.7.0 was
  introduced or left behind.

## Runtime checks (read-only, no repo state mutated)

- `python -m rumpun --version` — ran.
- `python -m rumpun season list` — ran, output matches documented format.
- `python -m rumpun season show s7` — ran; prints status line, per-agent
  deliverables, lane counts, confirming the new quickstart entry.
- `python -m rumpun board s7` — ran; same snapshot view as `season status`.
- `ruff check .rumpun/rimba/s7/w2/lane_tool.py` — All checks passed (repo
  config: line-length 100, select E/F/I/UP/B/SIM/RUF).
- `python lane_tool.py read ""` and a `start` append — ran; lane event
  round-trips through rumpun.collab.
