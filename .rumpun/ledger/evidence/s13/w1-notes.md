# s13 w1 — audit.py extensions: route outcomes, band calibration, budget flag

Base: `src/rumpun/audit.py` at commit `eddd3ba` (current main). This file is a
drop-in replacement; every existing behavior and all 41 suite tests pass
unchanged (`tests/` untouched).

## Trigger rules (exact)

**F4 route outcomes** — per route, over finalized agent snaps in the audited
window. A snap is an entry of `agents` in `rimba/<sid>/_season/state.json`
(the engine writes it at finalize; a running season has no `agents` block and
contributes nothing).

- deliverable = any file under `rimba/<sid>/<name>/` (recursive) whose
  workspace-relative path has **no** component in
  `{agent.log, exit, prompt.md, prompt-meta.yaml, state.json, terminated,
  terminated.tmp, __pycache__}` — so `__pycache__/*.pyc` stays bookkeeping,
  `sub/notes.md` counts.
- classification order: `exit_code == 0` → clean-deliverable / clean-empty on
  deliverable presence; `exit_code` non-null → failed; `state == "failed"`
  (unparseable `exit` file, engine semantics) → failed; else (terminated,
  crashed, stalled, running) → not-exited. `state == "exited"` with
  `exit_code` None cannot occur (engine contract) and would classify
  not-exited rather than guess.
- finding line per route (route name order): `route R: A clean-deliverable,
  B clean-empty, C failed, D not-exited over N spawns (sids)`. The sid list is
  every season the route spawned in — same set as the finding, not only the
  clean-empty seasons.
- candidate: `clean-empty >= 2` per route → "route R: B clean-empty spawns —
  add spawn tool-check or prefer alternative route"; band "WIN when
  clean-empty rate drops to 0 or a tool-check lands". Two clean-empty inside
  one season trigger (s6 pattern); no window-size gate.

**F5 band calibration** — per engine season holding `results.jsonl`
("harvested"). Integrated count = rows with `"integrated": true` (JSON
boolean true only; strings ignored). Season verdict = last `verdicts.jsonl`
row whose `season` == sid (the report verb's rule [H]; no such row → no
verdict, no finding). Finding per season with verdict LOSS and integrated
>= 1: "LOSS season <sid> shipped K integrated module(s) — band masked value".
Candidate at >= 2 such seasons: "recalibrate LOSS bands — count integrated
deliverables in the band"; band "WIN when no later LOSS season ships an
integrated module its band ignores" (band text not pinned by the task; kept
in the house candidate format).

**F6 budget compliance** — finding only, never a candidate:
`campaign_cost_cap unset since campaign start (P9) — operator sets the
number; the tool only flags`. Fires when the cap is null or absent. A set
value is never interpreted (no type check, no comparison) — presence is all
the tool judges.

## Priority under the cap (MAX_CANDIDATES = 3)

1. dead-phase triggers, pipeline order (existing, unchanged, still gated on
   n >= 2 engine seasons)
2. route triggers, route name order
3. band-calibration trigger (one proposal, cites the masked seasons)
4. stall trigger (existing, unchanged — kept last per the s11 record contract
   "phases in pipeline order first, stall trigger last"; the task's list
   names phase → route → calibration → budget and leaves stall's slot to the
   existing rule)
5. budget flag — finding only, never occupies a candidate slot

Overflow is named, never invented: labels of dropped proposals appear after
"candidate cap 3 reached in pipeline order". One deliberate wording change:
that line now reads "also **triggered** but unproposed here" (was "also
**unexercised** but unproposed here", phase-only phrasing that mislabels
dropped route/calibration triggers). No test pins the old wording.

## Decisions worth flagging

- Budget key path: the task says `campaign.budget.campaign_cost_cap`; the
  file as `scaffold.py` writes it (and the live `rumpun.yaml`) holds the key
  at top-level `budget.campaign_cost_cap`. I read the file layout — one
  mechanism, not a two-path guess.
- `cli.py` needs no change: `run_audit` signature and `candidate_lines`
  contract are untouched (proven by the smoke run printing candidates through
  the verb's own path).
- `results.jsonl` corrupt lines refuse the audit with file:line, same rule as
  `verdicts.jsonl` (shared `_read_jsonl`); `_season_status` folded into
  `_season_state` (one read feeds F2 status and F4 snaps; identical error
  semantics, no external callers).

## Left out (on purpose)

- No per-benih (per-name) tables — grouping is per route, as specced.
- No route preference or tool-check automation — the candidate proposes;
  evolve gate decides.
- No band-masked candidate below 2 seasons (single season = finding only).
- No reading of a nested `campaign.budget.*` path, no cap-value validation,
  no cost aggregation — the cap is a flag, not a meter (P24 owns the meter).
- Nothing outside the audited window is read; nothing but the akar record is
  written (musim/rimba byte-identical after a run, sha-checked).
- No edits to `src/`, `tests/`, or `cli.py` — harness merges this file.

## Verification (all on this exact file, repo untouched)

- ✅ suite: 41/41 pass with this audit.py substituted into a /tmp package
  copy (`PYTHONPATH` swap; `import rumpun.audit; __file__` points at the
  copy). `ruff check --line-length 100` clean (audit.py, lane_tool.py).
- ✅ 13/13 synthetic edge checks (/tmp/s13w1_edge.py): classification matrix
  incl. pycache-only workspaces; single-season double clean-empty trigger;
  cap-3 order phases → route → calibration with overflow naming both dropped
  labels; cap set/null; corrupt results.jsonl refusal; WIN-with-integrated
  non-finding; string `"true"` not counted as integrated.
- ✅ real-ledger smoke on a /tmp copy of `.rumpun` (window s5–s14; s14.yaml
  exists untracked, s4 falls out): record `audit-2` appended in the copy;
  F4 `route glm: 11 clean-deliverable, 6 clean-empty, 0 failed, 0 not-exited
  over 17 spawns (s5..s12)`; F5 masked: s5, s6, s12 (2 each); F6 fires; two
  candidates (route, calibration); musim/ + rimba/ sha256-identical before
  and after.
- Python 3.10+ only via `from __future__ import annotations` (suite ran on
  3.13); stdlib only.
