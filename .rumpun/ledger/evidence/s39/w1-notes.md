# s39 w1 — honest season counts in the usefulness brief

## Task
`tools/usefulness_audit.py` counts every `musim/s<N>.yaml` as a season
(`season_count`), including seeded drafts that never ran. The decade-3
review's own residual flagged the inflation ("The headline counts 34
seasons, but the ledger lists 33 identifiers ... Season count therefore
overstates completed, assessed work"). Fix in the brief composition: the
brief reports run seasons (musim yamls whose sid has a rimba state file)
and drafted-only yamls (without one) verbatim in the headline, e.g.
"3 run, 2 drafted-only, 5 total". The decade trigger arithmetic
(`floor(total/10)`) is unchanged.

## Finding
- `season_count` (tools/usefulness_audit.py:133) counts every matching
  yaml. The brief headline and facts line carried only that total.
- The run/drafted distinction is operational: audit-28 scopes "engine
  seasons with rimba/ (9) of 10" musim seasons.
- State-file criterion: `rimba/<sid>/_season/state.json` — the engine's
  season state file (referenced by `rollback_season`'s docstring in
  evolve.py:410; the test fixture `_write_rimba_season` writes exactly
  this path).
- Real ledger today: 40 musim yamls, 38 run (s2–s39), 2 drafted-only
  (s1 — `rimba/s1/` holds only `manual-run/`; s40 — seeded, no rimba
  dir). Both drafted cases covered by the same criterion.

## Change (patched copy only; repo untouched)
`copy/tools/usefulness_audit.py`, seven hunks (see `patch.diff`):
1. Module docstring: one sentence stating the honest-count brief rule.
2. New `season_split(root) -> tuple[int, int]` — (run, drafted-only) by
   `rimba/<sid>/_season/state.json` presence. `season_count` untouched.
3. `compose_brief` signature gains `run_count, drafted_count`; docstring
   notes `count` stays the total (decade-math input).
4. Headline: `...the ledger holds {count} musim seasons ({run} run,
   {drafted} drafted-only, {count} total).`
5. Facts line: `musim seasons: {run} run, {drafted} drafted-only,
   {count} total`
6. `run()`: split + sum guard — refuses when `run + drafted != count`
   (new honest refusal, fires before any route invocation).
7. `run()`: `compose_brief` call passes the split.

Deliberately unchanged: `season_count` itself, `due_decade` (still
`floor(total/10)`), and the record body line `seasons: {count} musim
seasons at audit time` (the task scopes the fix to the brief; the record
line is the true ledger total at audit time and feeds no arithmetic).

## Repro (repro_honest_counts.py → repro_output.txt)
17 checks, 0 failed, exit 0.
- unit fixture (3 run + 2 drafted-only): `season_count` 5, `season_split`
  (3, 2), headline renders
  "This is the decade-1 review: the ledger holds 5 musim seasons (3 run,
  2 drafted-only, 5 total).", facts line carries the same fragment, and
  the decade math is unchanged: floor arithmetic still total-driven
  (5→None, 9→None, 10→1, 40 with {1,2,3} covered→4, all covered→None).
- e2e through the patched tool (10 run + 2 drafted-only, 12 total,
  decade 1 due): runner exit 0, stub route executed, one
  usefulness-decade-1 record appended, record keeps the unchanged total
  line ("seasons: 12 musim seasons at audit time"), and the stub-echoed
  brief captured as evidence carries "10 run, 2 drafted-only, 12 total"
  exactly twice (headline + facts line).
- guard: forced `season_count` 6 against split 2+2 → refuses with
  "does not sum to season count 6"; nothing appended.
- Real ledger (observation, not a gate): total=40, split (38, 2).

## Suite
(suite result appended when the run completes)

## Decisions
- Drafted-only criterion is the state file, not the rimba dir: s1 has a
  rimba dir with only `manual-run/` and counts drafted-only, matching
  audit-28's "seasons with state.json" phrasing.
- The sum guard is new refusal surface; exercised in the repro via a
  simulated scan mismatch. The engine never produces the mismatch state.
- Repro bug fixed mid-run: part C's `season_count` monkeypatch leaked
  into part D's real-ledger observation (printed total=6); restored the
  original in a `finally` and reran — the recorded output is from the
  fixed run.
