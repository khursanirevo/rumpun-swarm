# s58 w1 notes — epics as data (declaration + rollup verb)

Shipped and verified. `rumpun epics` renders the epic rollup from
.rumpun/epics.yaml; `--init` scaffolds it; the declaration lints (id shape,
member existence, double membership); DESIGN section 16 carries the
epics-format note. The ledger was never written by this feature.

## What changed (workspace copies; the harness merges)

- `src/rumpun/epics.py` — NEW: the declaration module (epics_path, season_ids,
  scaffold, init, has_run_state, season_verdict, render).
- `src/rumpun/cli.py` — additive: cmd_epics, the `epics [--init]` parser
  block, cmd_lint dispatches an epics.yaml path to lint_epics, EpicsError in
  main()'s handled-error tuple, one docstring line. Nothing removed.
- `src/rumpun/lint.py` — additive: EPIC_ID_RE and lint_epics(); imports paths
  for the season-yaml scan. Nothing removed.
- `DESIGN.md` — workspace copy: `### s58 — epics as data (2026-09-16)`
  appended at the end of section 16.
- repo `src/` untouched: git status shows only corpus-pin side effects
  (replay-matrix.md, logs/), no source edits.

## Verified — ✅ real, run in scratch/ against real season data

| check | command | result | evidence |
|---|---|---|---|
| missing file | `rumpun epics` | flat hint, rc=0, no error | 1-hint.txt |
| --init scaffold | `rumpun epics --init` | campaign epic, seasons s1–s58, goal from rumpun.yaml, rc=0 | 2-init.txt, 3-epics-scaffold.yaml |
| --init refusal | second --init | error rc=1, file untouched | 5-init-refusal.txt |
| campaign render | `rumpun epics` | `campaign  s1-s58  4 WIN / 1 LOSS / 0 other  campaign  (no run state: s1, …, s58)`, rc=0 | 4-render-campaign.txt |
| two-epic render | `rumpun epics` | `close-arc  s54-s57  4 WIN / 0 LOSS / 0 other  the close arc` and `early-loop  s12-s58  0 WIN / 1 LOSS / 0 other  the early loop  (no run state: s58)`, rc=0 | 9-render-two-epics.txt |
| duplicate member | `rumpun lint <epics.yaml>` | `season 's54' is a member of two epics: 'alpha' and 'beta'`, rc=1 | 8-lint-dup.txt |
| duplicate via verb | `rumpun epics` | findings logged, rows still render, rc=1 | 10-verb-dup-exit1.txt |
| bad epic id | `rumpun lint <epics.yaml>` | `epic id 'Bad_Id' does not match ^[a-z0-9][a-z0-9_-]*$`, rc=1 | 7-lint-badid.txt |
| unknown member | `rumpun lint <epics.yaml>` | `member season 's99' does not exist as a season yaml id`, rc=1 | 11-lint-unknown-member.txt |
| clean declaration | `rumpun lint <epics.yaml>` | lint OK, rc=0 | 6-lint-clean.txt |
| ruff | `ruff check --no-respect-gitignore` on the three files | All checks passed, rc=0 | 12-ruff.txt |

Verdict provenance: WIN/LOSS counts rest on the harvest verdict rows
(runs/<sid>/verdicts.jsonl, the last row naming the season wins); the LOSS is
s12's real row; s58 has a season yaml but no runs state in the scratch
campaign, so it is marked on the line and never counted.

## Suite floor — ✅ measured (257 items)

| run | tree | result |
|---|---|---|
| 1 | scratch, pre-fix tree (lint.py missing its paths import) | 255 passed, 2 failed |
| 2 | scratch, fixed tree | 255 passed, 2 failed |
| solo ×2 | stop-race pin, scratch tree | passed, passed |
| solo | stop-race pin, repo src baseline | passed |

The two in-suite reds, neither in the epics code:

- `test_s38_coldstart_checker_leaves_repo_rumpun_untouched` — structural
  under a live season. Its own assertion output names the mutation sources:
  `.rumpun/runs/s58/w1` and `w2` agent.log/state.json, plus w2's notes.md
  landing between the snapshots; the checker itself exited 0 (11/11 steps).
  The pin cannot pass while s58 runs; it should be green at merge time.
- `test_stop_racing_spawn_tracks_and_kills_every_spawn` — the race family
  under full-suite load. Solo warm runs pass on BOTH trees (scratch with the
  epics code and repo baseline without it), so the change is not the cause.
  Related: the h6 replay row flaked in run 1 (stale tree) with its own
  "timing-dependent, rerun before escalating" note and PASSED in run 2 on
  the fixed tree; the fresh matrix row reads PASS, race window 0/20.

Suite side effect to expect at merge: the corpus-gate pin re-ran the corpus
during both suite runs and refreshed `replay-matrix.md` and `logs/s1*.*` in
the repo working tree. Uncommitted, not mine to commit; the only working-tree
delta.

## Constraints held

- Ledger: zero writes (append-only preserved; the feature reads runs state
  and verdict rows only).
- tests/: untouched (w2 owns the pins).
- Workspace rule: every write sits in .rumpun/runs/s58/w1/; repo src/ is
  untouched — cli.py and lint.py ship as workspace copies for the merge.
- Diagnostics via logging; print only for rendered data rows, matching the
  file's own verb convention (season list, direct, audit candidates).
