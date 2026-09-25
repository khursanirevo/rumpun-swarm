# s23 w1 notes — M2 declared-artifact liveness + M8 id high-water mark

Date: 2026-09-15. Workspace: `.rumpun/rimba/s23/w1/`. All writes stayed in
this workspace (scratch/base, scratch/patched, scratch/repro, this file);
nothing in the repo tree was touched. Diffs and runs are recorded under
`scratch/repro/`.

## What changed (patched copies in scratch/patched, diffed vs scratch/base)

- `src/rumpun/audit.py` — M2
  - `LEDGER_ARTIFACTS` and `_season_artifacts` are gone. For each phase the
    latest season declares, every audited season's OWN yaml now decides: a
    season counts toward that phase's denominator only when its own
    methodology.pipeline declared the phase (a pre-phase season is no
    evidence either way) and it is not still running (a running season has
    not reached the phase yet). The numerator checks that season's own
    declared writes filename for existence at rimba/<sid>/ — the reviewer's
    declared `custom.jsonl` present in every season now counts as liveness.
  - `_season_running(state)` is the completed test: recorded status ==
    "running" excludes; a season with no state.json is not provably running
    and counts (the s13 base-fixture contract: the "1 of 2" pin has an
    empty rimba/s2 dir, so no-state must stay in the denominator).
  - F1 line shape unchanged: `F1 phase liveness: phase P (writes W) wrote
    its artifact in K of N engine seasons (ids)` — K and N are now
    per-phase numbers.
  - Candidate trigger compatibility: the window-wide gate stays (`n >= 2`
    engine seasons), plus `k == 0 and n_completed >= 1`. This exact
    combination keeps every s13 pin green, including
    test_audit_candidate_priority_phase_route_calibration, whose dead phase
    `reflect` is declared only by the latest season (per-phase denominator
    1, window gate 2 — candidate still fires first). The `n_completed >= 1`
    half suppresses a nonsense "0 of 0" candidate when only a running
    latest declares the phase.
  - The states read moved above F1 (one `_season_state` read feeds F1/F2/F4).
- `src/rumpun/evolve.py` — M8
  - `draft_next` numbering: `next_id = s{_high_water_mark(root) + 1}` — no
    longer `latest + 1`. The parent-must-be-latest check and the
    target-exists guard are unchanged.
  - `_high_water_mark(root)` = max season number ever allocated over three
    sources: top-level `musim/s<N>.yaml`, files under `musim/rejected/`
    (rejected drafts and rolled-back seasons), and akar lifecycle record
    ids `reject-s<N>` / `rollback-s<N>`.
  - Mechanism choice (task allowed scan or counter file): scan, no counter
    file. The akar ledger is append-only evidence; the mark derives fresh
    on every draft and no mutable counter state can drift from what the
    records say. Documented in the `_high_water_mark` docstring and the
    module docstring.
  - `_latest_season` refactored onto a shared `_season_numbers(directory)`
    scanner; behavior unchanged.
- `src/rumpun/akar.py` — M8 support (additive; akar.py is not on the
  do-not-touch list)
  - `declared_ids(root)` — public read view returning the declared
    record-id -> file map from the same scan `append_record`/`find_record`
    guard with. The HWM reads declared ids (the H8 resolution rule), not
    filenames, so a filename/declared-id mismatch cannot hide an id.

Untouched: lint.py, collab.py, engine.py, cli.py, report.py, tests/,
yamlio.py, graph.py, routes.py, scaffold.py, harvest.py, DESIGN.md.
`diff -ru scratch/base/src scratch/patched/src` shows exactly three changed
files (scratch/repro/diff_base_patched.txt, read back line by line).

## Evidence (captured in scratch/repro/)

Environment: pytest 9.1.1 (repo .venv), ruff (system, --no-respect-gitignore
because rimba/ is gitignored), python 3.13. Suite invoked as
`PYTHONPATH=src pytest tests/ -q` inside each copy; repro scripts take the
copy dir as argv[1] and insert <copy>/src at sys.path[0].

- Full suite: base copy 108 passed (32.1s, out_suite_base.txt); patched
  copy 108 passed (32.3s, out_suite_patched.txt) — same count, zero
  failures, s13 audit pins included. Final run is on the final patched
  state (after the fixes listed below).
- `repro_m2_liveness.py` (out_m2_patched.txt / out_m2_base.txt):
  - patched: GREEN 6/6, EXIT=0 — S1 two seasons declaring
    collect->custom.jsonl, both wrote it: F1 counts "2 of 2", NO dead-phase
    candidate; S2 a pre-phase season (older yaml lacks the phase) is
    outside the denominator: "1 of 1", no candidate; S3 a running latest
    declaring the phase is excluded: "1 of 1", no candidate.
  - base (pre-fix): RED 0/6, EXIT=1 — all three scenarios show the false
    evidence (S1 "0 of 2" + exercise-or-trim candidate on an artifact that
    exists everywhere; S2 "0 of 2" + candidate; S3 "1 of 2").
- `repro_m8_hwm.py` (out_m8_patched.txt / out_m8_base.txt):
  - patched: GREEN 12/12, EXIT=0 — reject latest s2 then draft from s1
    gives musim/s3.yaml (id s3, parent s1), s2 NOT re-issued; adding
    musim/rejected/s4.yaml + a rollback-s4 akar record then drafting from
    s3 gives musim/s5.yaml — all three mark sources raise the mark.
  - base (pre-fix): RED 3/12, EXIT=1 — the reviewer reproduction fires:
    the post-reject draft re-uses s2 (musim/s2.yaml recreated with id s2,
    colliding with the reject-s2 record); step 2 checks fail downstream of
    the reuse. ("s4 not re-issued" is trivially green on base: base never
    reached s4.)
- ruff check --no-respect-gitignore: clean on scratch/patched/src and on
  both repro scripts.
- Readback gate: the full unified diff was read back after every edit
  round; the final diff (100 added lines over three files) contains the
  fixed lifecycle regex (diff line 173) and nothing unintended.

## Defects found and fixed during this work (recorded for honesty)

- Three write-corruption incidents in files I generated (the known
  pattern): a stray `F1 :=` inside an assert in the first M2 repro, and
  `I_AM_CORRUPT` / `"uuid" if False else` fragments in the first M8
  script. All caught by re-reading the written file before any run and
  rewritten cleanly.
- The first M8 script crashed with KeyError 'minutes': the fixture YAML
  template goes through str.format, so `budget: {minutes: 1}` needed
  doubled braces (the s13 fixture does this; I missed it). Fixed.
- **The M8 repro caught a real defect in my own first patch**: the
  lifecycle regex captured `s<N>` with the letter and `int("s2")` raised
  ValueError inside `_high_water_mark`. The 108-test suite cannot see this
  (no suite test combines lifecycle records with draft numbering — exactly
  the untested seam M8 closes); the repro hit it on the first patched run.
  Fixed to `-s(\d+)` capturing digits only; suite and repro re-run green.

## Notes for merge

- w2 owns tests/: the repros port directly as pins — M2: the three
  scenarios above (custom.jsonl 2-of-2, pre-phase ignored, running
  excluded); M8: reject-latest-then-draft skips the id, and rejected-file /
  rollback-record sources raise the mark. One boundary worth pinning
  explicitly: a season with NO state.json counts toward the F1 denominator
  (only recorded status "running" excludes) — that boundary is load-bearing
  for the s13 "1 of 2" pin.
- akar.py change is purely additive (one new function); merge surface is
  audit.py and evolve.py.
- LEDGER_ARTIFACTS is removed; grep confirmed no importer outside audit.py
  (before removal). If anything downstream wants the canonical artifact
  list back, it should derive from the season yaml, not a fixed tuple.
- Existing F1-F6 line shapes: F1 keeps its exact template; the candidate
  line's "written in 0 of N" now reports the per-phase completed
  denominator (the s13 pins assert substrings and ordering, not the number
  — all green).
