# s66 w2 — spec-first pins for the kanban verb

Deliverable: `tests/test_s66_w2_pins.py` (in this workspace; graft into
repo `tests/` at merge). Status: measured red, 3/3, red for the spec
reason. w1 owns `src/rumpun/cli.py` and turns the pins green.

## Spec anchors

- Directives seq 7 (.rumpun/ledger/directives.jsonl): kanban columns
  backlog (armed candidates + unfilled seeds), doing (the running season),
  need-human (unset cap, waiver requests, autonomy promotion), done
  (harvested seasons with verdict + salvage marks); rendered by a verb
  (`rumpun kanban`) from the ledger and runs state, no new state file.
- Seq 8 addendum: every NEED HUMAN card carries four plain sentences —
  what happened, what needs doing, why it needs a human, what happens if
  nobody acts; no card ships without them.
- Seq 10: i-have-adhd default — rumpun output in adhd-actionable shape;
  the four-sentence card is that shape on the board.
- audit-42 F6: "campaign_cost_cap unset since campaign start (P9) —
  operator sets the number; the tool only flags" — the unset cap is the
  live NEED HUMAN trigger the seq-8 card pins.
- s65-harvest: containment landed WIN; the s65 w2 pins are the shape
  precedent (bounded subprocess pins over throwaway campaigns).

## Measured red set (run 1, 2026-09-16, log /tmp/s66w2-run1.log)

Environment: uv venv python 3.13.12, pytest 9.1.1, repo root
/mnt/data/work/rumpun, pins run solo from the w2 workspace
(`uv run python -m pytest <file> -v`).

- Result: 3 failed, 0 errors, 6.95s.
- Pin 1 `test_s66w2_kanban_renders_all_four_columns`: red at the kanban
  exit assert. `rumpun kanban` exits 2, argparse "invalid choice:
  'kanban'" (choose from init, lint, graph, models, direct, board,
  harvest, audit, epics, check, waive, plugin, season, evolve).
- Pin 2 `test_s66w2_need_human_card_carries_four_sentences`: same red,
  exit 2 invalid choice.
- Pin 3 `test_s66w2_fresh_campaign_renders_empty_and_writes_nothing`:
  same red, exit 2 invalid choice.
- Zero "fixture defect" failures: in every pin the fixture chain held
  before the red — lint clean, both real stub starts persisted completed,
  hand-built done artifacts accepted, running state written, and pin 1's
  real `rumpun audit --last 10` appended audit-1 with the armed candidate.
  Every red names the missing verb, none names the fixture.

## Post-merge expectations (what green requires from w1)

- `kanban` in the argparse subcommand list; exit 0 on render.
- Column headers as lines starting with backlog / doing / need[-_ ]human /
  done (case-insensitive); region = up to the next header line.
- backlog names the newest audit record's candidate trigger text
  ("exercise or trim phase execute").
- doing names the running season by id (persisted status "running").
- done counts its seasons (digit 2) and carries WIN, LOSS, "salvaged".
- Unset-cap card: names campaign_cost_cap or "cost cap", exactly four
  sentences, themes in seq-8 order (anchor regexes in the pins file,
  S66W2_THEMES).
- No write to the campaign tree during the render (file-snapshot equality
  in pins 1 and 3).

## Fixture decisions the merge should know

- The real `rumpun harvest` verb is never called by the pins. cmd_harvest
  also runs _run_check: the s55 checker subprocess under the repo venv
  python with cwd=repo and default out-dir, which appends a check-<sid>
  record into the REAL campaign ledger. Fixture closes are hand-built in
  the exact harvest.py shapes instead (verdicts.jsonl row plus sha-sealed
  <sid>-harvest record, salvage via "salvaged": true and "(salvaged)"
  title).
- The running season is hand-persisted in the engine's own start shape
  (engine.py start dict; the live s66 season state.json is that shape). A
  real background start would race the render (the s21 dual-start race).
- Real verbs exercised: lint, season start (stub route, no quota, no
  network), audit --last 10 (appends into the fixture ledger only).
- Backlog in the fixture also carries an unfilled seed (s652 yaml, no run
  state). Seq 7 puts unfilled seeds in backlog; the pins do not assert it
  (task pin 1 scope is the armed candidate), so either rendering passes.

## Environment notes

- System python3 is banner-blocked in this repo (uv-nag sitecustomize,
  rc=1). Run tests via `cd /mnt/data/work/rumpun && uv run python -m
  pytest ...`; ruff at ~/.local/bin/ruff check --no-respect-gitignore
  (clean on the pins file, line-length 100, py310 target).
- Suite floor: w2 wrote only inside .rumpun/runs/s66/w2 (tests/ additions
  only, untracked by the merge); no repo-tracked file changed, so the
  floor is untouched by this work. Post-merge the harness reruns the full
  suite with the pins grafted; shared-lane caveat: w1 edits src/ in the
  same worktree, so floor runs should follow the s64 shared-lane split
  (certify the floor, probe py_compile first).
