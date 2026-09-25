# s11 w2 — spec-first tests for audit.run_audit

Deliverables in this workspace only; nothing outside it touched.

| file | what it is |
|---|---|
| test_rumpun.py | repo tests/test_rumpun.py verbatim + one docstring paragraph + one import + 10 audit tests |
| lane_tool.py | posts/reads build-lane events via RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK |
| notes.md | this file |

## Added — 10 tests under `# --- audit reflection (w2 s11 scope, spec-first) ---`

Fixtures: `AUDIT_SEASON` (two-phase pipeline — execute writes results.jsonl,
evaluate writes verdicts.jsonl), `_write_audit_proj` (rumpun.yaml manual
stage, musim seasons, empty akar/), `_write_rimba_season` (artifacts +
_season/state.json), `_audit_base` (s1 completed + full artifacts, rimba/s2
empty), `_tree_snapshot` (byte map of a subtree).

| test | spec line it pins |
|---|---|
| test_run_audit_first_record_is_audit_1 | return value is under akar/, file name and text contain audit-1 |
| test_run_audit_second_run_writes_audit_2 | second run on the same root writes audit-2; the first record survives (append-only) |
| test_run_audit_dead_phase_names_phase_and_season | a season with no rimba dir yields a finding whose line names the phase (execute, evaluate) and cites the season id |
| test_run_audit_liveness_line_and_alive_negative | body has "wrote its artifact in 1 of 2"; 1-of-2 alive does NOT yield "exercise or trim" |
| test_run_audit_zero_artifacts_yield_exercise_or_trim | phase with 0 artifacts across 2 rimba seasons yields a candidate line naming the phase |
| test_run_audit_single_stall_finding_no_resize | one stopped_stall season: finding cites the sid and says stall; "re-size" absent |
| test_run_audit_two_stalls_yield_resize_candidate | two stopped_stall seasons: "re-size" present |
| test_run_audit_never_modifies_musim_or_rimba | byte-level snapshots of musim/ and rimba/ identical before and after |
| test_run_audit_last_n_takes_highest_season_numbers | last_n=1 scans only the highest-numbered season; liveness reads "1 of 1" |
| test_run_audit_duplicate_id_wraps_into_audit_error | a non-audit-named file declaring id audit-1 -> akar duplicate-id error surfaces as audit.AuditError |

Beyond the five required tests: liveness content + alive-negative, the
exercise-or-trim candidate, the AuditError wrap (all named in the spec),
and the last_n window.

## Interpretation calls (spec-first pins; flag at integration if w1 differs)

- N in "K of N" = seasons in the last_n scan window (musim-driven), not the
  count of rimba dirs on disk.
- The "exercise or trim" guard (>= 2) uses the same window count.
- next_index counts audit-* FILES in akar/ per the spec, not declared ids:
  the wrap test plants `occupied.md` declaring `id: audit-1`, which leaves
  the count at 0, so run_audit reuses audit-1 and hits the duplicate. If w1
  counts declared ids instead, that test goes red at integration — that is
  the divergence it exists to catch.
- A healthy scanned season need not be named in the record; findings carry
  the sids. The last_n test pins selection via "s1" absent + "1 of 1"
  (s1 has no rimba dir, so a wrong window would read "0 of 1" citing s1).
- Phases are declared under methodology.pipeline[].{phase, writes}, the
  repo convention from SEASON_S1; the spec does not say where else they
  would live.

## Left out

- No CLI e2e (`python -m rumpun audit`): the spec is the library function;
  verb wiring is w1's scope.
- No test for corrupted musim yaml / state.json: the spec names no error
  contract for those (only the akar duplicate wrap), so nothing to pin.
- No assertion on record title/date wording beyond the required strings.
- No pin on the <2-seasons guard boundary of "exercise or trim" (one rimba
  season, 0 artifacts): it diverges under the file-count vs window-count
  readings of the spec and is not load-bearing for the minimum list.
- No last_n=0 or negative last_n: spec silent; garbage-in behavior untested.

## Verification — all measured, 2026-09-14

- `ruff check` on both .py files: clean (line-length 100, py310 target).
- `diff tests/test_rumpun.py` vs the workspace copy: only the docstring
  paragraph, the audit import, and the appended section differ; the
  existing 31 tests are byte-identical.
- Repo suite untouched: `python -m pytest tests/test_rumpun.py -q` ->
  31 passed.
- Spec check: a scratch spec-faithful audit.py (outside the repo, in
  /tmp/rumpun-audit-speccheck, deleted after the run) — the workspace
  suite read 41 passed (31 + 10) against it. The scratch found two real
  defects in this pass: a scratch sid-extraction bug (fixed in the
  scratch) and one over-pinned assertion here ("s2" must be named in a
  healthy season's audit; removed — findings, not liveness, carry sids).
- Pre-integration red, as designed: against repo rumpun the workspace file
  fails collection with exactly `ImportError: cannot import name 'audit'
  from 'rumpun'` — nothing else is red. The suite reads 41/41 once w1's
  module lands.
- Lane: start posted (seq 0); policy/done posted at close; lane read back
  in full afterwards. Never waited on w1.
