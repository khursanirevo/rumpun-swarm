# s28 w1 notes — README rewrite to current truth

## What was verified by execution (✅)

- `rumpun --version` printed `0.11.0`. Matches `pyproject.toml` (`version = "0.11.0"`)
  and `src/rumpun/__init__.py` (`__version__ = "0.11.0"`).
- `rumpun init init-check` run inside this workspace: scaffolded `rumpun.yaml`,
  `musim/s1.yaml`, `musim/_template.yaml`, `prompts/base/` (7 phase prompts),
  `README.md`, `akar/`, `rimba/`. Matches the Quickstart claim.
- `rumpun lint init-check/.rumpun/musim/s1.yaml` on the fresh scaffold: exit 1,
  errors `goal is empty`, `metric is empty`. Confirms "lint blocks while the
  season fields are empty".
- `rumpun graph` on the fresh scaffold prints the lean 2-phase DAG
  (execute -> results.jsonl -> evaluate); on `.rumpun/musim/s1.yaml` it prints
  the legacy 7-phase DAG. Exit 0 both.
- `rumpun season list` on this repo: `s1  no state`, then completed /
  stopped_stall rows with durations and agent counts. Confirms the `no state`
  caveat.
- `rumpun models` (read-only): prints CLI presence table and route spawn
  commands. No `--write`, no `--probe` run.
- `MAX_CANDIDATES = 3` read at `src/rumpun/audit.py:48` — the "at most 3
  candidates" claim.
- mtime caveat read at `src/rumpun/engine.py:388-400` (growth-only progress;
  `last_size=None` keeps the s15 mtime estimate) — matches s23/s24 M10.
- Report-snapshot basis read at `src/rumpun/report.py:480-515` (renders from
  persisted state; running seasons listed from persisted state).

## Full CLI help capture (paste target for the verb check)

Top level `rumpun --help`:

```
usage: rumpun [-h] [--version]
              {init,lint,graph,models,direct,board,harvest,audit,season,evolve} ...

rumpun CLI — verb dispatch (layout per ratified P36 D9). Top-level: init,
lint, graph, models, board, harvest, direct, audit. Groups: season
start/stop/status/list/show/report, evolve plan/approve/apply/reject/rollback.
Implemented (v0.11.0): init, lint, graph, models, board, harvest, direct
[--list], audit [--last], season start/status/stop/list/show/report (report
--serve), evolve plan/apply/approve/reject/rollback. harvest carries optional
--band/--observed (s24): the season verdict row keeps the declared band and
observed result again instead of empty strings. The stub registry is empty:
every P36 D9 verb exists; unknown verbs exit 2. audit is the phase-2
reflection verb (DESIGN section 15): it reads the season ledger and appends
evidence-cited candidate mutations. Build order lives in DESIGN.md section 10.

positional arguments:
  {init,lint,graph,models,direct,board,harvest,audit,season,evolve}
    init                scaffold a rumpun project in TARGET
    lint                validate a season YAML (structure, DAG, contracts,
                        citations)
    graph               render a season pipeline as mermaid
    models              detect spawnable model routes on this machine
    direct              append or list operator directives (P8)
    board               live season board (P36: snapshot form)
    harvest             tuai: close a season into akar (step 4)
    audit               reflect over the season ledger; append evidence-cited
                        candidates (DESIGN 15)
    season              season lifecycle commands
    evolve              evolution commands (evolusi)

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
```

`rumpun init --help`:

```
usage: rumpun init [-h] [target]

positional arguments:
  target

options:
  -h, --help  show this help message and exit
```

`rumpun lint --help`:

```
usage: rumpun lint [-h] file

positional arguments:
  file        season YAML path

options:
  -h, --help  show this help message and exit
```

`rumpun graph --help`:

```
usage: rumpun graph [-h] file

positional arguments:
  file        season YAML path

options:
  -h, --help  show this help message and exit
```

`rumpun models --help`:

```
usage: rumpun models [-h] [--write] [--probe]

options:
  -h, --help  show this help message and exit
  --write     fill rumpun.yaml routes: {} with the detected table
  --probe     send one tiny completion per claude route (spends quota)
```

`rumpun direct --help`:

```
usage: rumpun direct [-h] [--list] [text]

positional arguments:
  text        directive text; recorded with status pending

options:
  -h, --help  show this help message and exit
  --list      print all directives, pending first
```

`rumpun board --help`:

```
usage: rumpun board [-h] id

positional arguments:
  id          season id, e.g. s1

options:
  -h, --help  show this help message and exit
```

`rumpun harvest --help`:

```
usage: rumpun harvest [-h] --verdict {WIN,LOSS,NEUTRAL,INVALID}
                      --implies IMPLIES [--band BAND] [--observed OBSERVED]
                      id

positional arguments:
  id                    season id, e.g. s2

options:
  -h, --help            show this help message and exit
  --verdict {WIN,LOSS,NEUTRAL,INVALID}
  --implies IMPLIES
  --band BAND           expected band for the season metric; recorded verbatim
                        in the verdict row
  --observed OBSERVED   observed result for the season metric; recorded
                        verbatim in the verdict row
```

`rumpun audit --help`:

```
usage: rumpun audit [-h] [--last N]

options:
  -h, --help  show this help message and exit
  --last N    audit the last N musim seasons (default: 10)
```

`rumpun season start --help`:

```
usage: rumpun season start [-h] [--json] file

positional arguments:
  file        season YAML path

options:
  -h, --help  show this help message and exit
  --json      machine-readable output
```

`rumpun season stop --help`:

```
usage: rumpun season stop [-h] id

positional arguments:
  id          season id, e.g. s1

options:
  -h, --help  show this help message and exit
```

`rumpun season status --help`:

```
usage: rumpun season status [-h] [--json] id

positional arguments:
  id          season id, e.g. s1

options:
  -h, --help  show this help message and exit
  --json      machine-readable output
```

`rumpun season list --help`:

```
usage: rumpun season list [-h]

options:
  -h, --help  show this help message and exit
```

`rumpun season show --help`:

```
usage: rumpun season show [-h] [--json] id

positional arguments:
  id          season id, e.g. s1

options:
  -h, --help  show this help message and exit
  --json      machine-readable output
```

`rumpun season report --help`:

```
usage: rumpun season report [-h] [--serve] id

positional arguments:
  id          season id, e.g. s2

options:
  -h, --help  show this help message and exit
  --serve     after rendering, serve rimba/ over HTTP at http://localhost:8611
```

`rumpun evolve plan --help`:

```
usage: rumpun evolve plan [-h] file

positional arguments:
  file        parent season YAML path

options:
  -h, --help  show this help message and exit
```

`rumpun evolve apply --help`:

```
usage: rumpun evolve apply [-h] file

positional arguments:
  file        drafted season YAML path

options:
  -h, --help  show this help message and exit
```

`rumpun evolve approve --help`:

```
usage: rumpun evolve approve [-h] file

positional arguments:
  file        drafted season YAML path

options:
  -h, --help  show this help message and exit
```

`rumpun evolve reject --help`:

```
usage: rumpun evolve reject [-h] file

positional arguments:
  file        drafted season YAML path

options:
  -h, --help  show this help message and exit
```

`rumpun evolve rollback --help`:

```
usage: rumpun evolve rollback [-h] id

positional arguments:
  id          applied season id, e.g. s3

options:
  -h, --help  show this help message and exit
```

## Verb check: documented vs `--help`

Every verb row in the README table maps to a captured help above:
init, models, lint, graph, direct, board, harvest, audit,
season start/stop/status/list/show/report, evolve plan/apply/approve/reject/
rollback. Board and `season status` share `cmd_season_status` (cli.py);
`board` exposes no `--json` (confirmed in both help outputs).

## Claims NOT verified in this session (⚠️) — carried from records, not re-run

1. `uv pip install -e .` as the install path — not re-run. The `rumpun`
   binary already on PATH answered `--version` 0.11.0.
2. `season start` / `season stop` — not executed (spawns agents; blocks).
   Claims rest on cli.py source, help text, DESIGN 13-15.
3. `harvest` — not executed (appends to the repo's real akar ledger). The
   "second harvest refused" claim (s21 M3) is from the season record, not
   re-run here.
4. `audit` — not executed (appends to akar). Behavior from cli.py,
   audit-13..16 records (F1-F6 checks, zero-candidate records exist), and
   audit.py source.
5. `evolve plan/apply/approve/reject/rollback` — not executed (write musim/
   and akar). Behavior from cli.py docstrings, P33 in DESIGN, scaffold.
6. `direct` append — not executed (writes the repo's directives.jsonl).
   `direct --list` behavior from cli.py source.
7. `models --write` and `models --probe` — not executed (mutates config /
   spends quota). Flags confirmed in help text and cmd_models source.
8. `season report` render and `--serve` — not executed (writes rimba/,
   opens a port). Basis: report.py source read, P36/P37 records, DESIGN 15
   dashboard sections. Running-season-snapshot caveat is the s22 M1 rule
   ("renders from persisted state only") as recorded, not re-tested.
9. `tools/replay_corpus.py` and `tools/render_dashboard.py` — not executed
   here. Documented from their docstrings/argparse and the s25-s27 DESIGN
   rows (6 PASS / 47-48 SKIP corpus runs, two-pass render) as recorded.
10. Test-suite counts quoted in DESIGN (133/133 at s27) — not re-run; no
    suite count is cited in the README.

## Caveats carried into the README (per task, from season records)

- Running-season report snapshots (s21 remaining item, s22 M1 landed rule).
- mtime estimate for history-less callers (s23 M10, s24 reconciliation,
  engine.py 388-400).
- Lane events refine, never gate (DESIGN 14 standing mitigations, protocol v2).
