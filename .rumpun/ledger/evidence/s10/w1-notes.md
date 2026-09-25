# s10/w1 README sync — verification notes

Sources: `/mnt/data/work/rumpun/README.md` and
`/mnt/data/work/rumpun/src/rumpun/cli.py` at main, clean tree (commit 004cb56).

## Method

- Static read of `build_parser()` and the `cmd_*` handlers in cli.py.
- Runtime read-only checks: `rumpun --version` and `--help` on the parser
  groups (see below). No command that mutates `.rumpun/` was run; executing
  the quickstart end to end would write ledger/state outside this workspace.
- Delta check: the written README differs from the repo README by exactly the
  three intended changes (diff run after write).

## Runtime evidence

- `rumpun --version` -> `0.9.0`.
- `rumpun --help` -> verbs: init, lint, graph, models, direct, board,
  harvest; groups: season {start,status,list,stop,report,show}, evolve
  {plan,apply,approve,reject,rollback}. Docstring states the stub registry
  is empty.
- `rumpun board --help` -> usage `rumpun board [-h] id`; no `--json`.
- `rumpun evolve rollback --help` -> usage `rumpun evolve rollback [-h] id`;
  takes a season id, not a file.

## Changes vs the repo README.md

1. Removed the "Not implemented yet" section. Basis: `NOT_IMPLEMENTED` and
   `SEASON_STUBS` are empty dicts (cli.py:36, cli.py:38); `evolve
   approve/reject/rollback` have real handlers (cli.py:351-382) and parsers
   (cli.py:487-502). The old table described them as exit-2 stubs — stale.
2. Replaced the two standalone `evolve plan` / `evolve apply` quickstart
   entries with a "### Evolution loop" subsection after harvest, covering
   all five evolve verbs, one line each. Wording follows the handler
   docstrings: approve appends an akar record and never modifies the draft;
   reject moves the draft to `musim/rejected/` and records the on_reject
   policy (P33); rollback moves the applied season's YAML to
   `musim/rejected/`, records the containment, and never runs git.
3. Fixed board `--json` drift. The board parser takes only `id`
   (cli.py:433-435); `--json` exists on `season start` (cli.py:451),
   `season status` (cli.py:455), and `season show` (cli.py:473), not board.
   `rumpun board s1 --json` is an argparse "unrecognized arguments" exit 2.
   Old text claimed "both take `--json`"; new text says only `season status`
   takes it.

## Commands checked and left as written

- `rumpun init` — `target` optional, default `.` (cli.py:404).
- `rumpun models --write` — `--write` and `--probe` exist (cli.py:414-417).
- `rumpun lint FILE`, `rumpun graph FILE` — file positional (cli.py:407-420).
- `rumpun direct TEXT` and `rumpun direct --list` — text optional,
  `--list` flag (cli.py:422-431).
- `rumpun season start FILE` — lint preflight inside start (cli.py:203-205),
  consistent with the lint entry's "errors block season start".
- `rumpun season stop s1` — id positional (cli.py:459-461).
- `rumpun season show s1` — id + `--json` (cli.py:469-474).
- `rumpun season list` — no args (cli.py:457-458); `no state` line for
  missing state (cli.py:286-287).
- `rumpun season report s1` / `--serve` — `--serve` renders then serves
  `rimba/` at 127.0.0.1:8611, prints `http://localhost:8611/s1/report.html`,
  Ctrl-C exits 0 (cli.py:303-322).
- `rumpun harvest s1 --verdict WIN --implies "..."` — both flags required;
  verdict choices WIN|LOSS|NEUTRAL|INVALID (cli.py:439-441).
- `rumpun evolve plan/apply/approve/reject FILE` — file positional
  (cli.py:481-496).
- `rumpun evolve rollback s2` — id positional (cli.py:497-502).

## Version pins

No rumpun version appears anywhere in the README; the only requirement
stated is Python 3.10 or newer, unchanged from the repo README. Installed
and reported version is 0.9.0.

## Not verified

- End-to-end execution of the quickstart sequence (init through evolve):
  running it would create/modify `.rumpun/` state outside the s10/w1
  workspace, which this task forbids. Command validity was checked against
  the parser surface and runtime help text only.
