# s34 w1 — falsify_required enforcement in lint

## Verdict first

The enforcement landed and every repro is green. Baseline suite 161/161 on
repo code. The patched suite is 152 passed / 9 failed: all 9 fail with
exactly the new error on the tests' shared minimal season fixture (a
no-reading-phase season, invariant declared) — the pins w2 owns, per the
s34 split. Two honest nuances below (template/seed stubs, and what C3 can
and cannot prove). All numbers below are measured this session.

## What landed

src/rumpun/lint.py (patched copy at this workspace's src/): one 21-line
block after the falsify pre-registration check, before evidence citations.
- Gate: `if "falsify_required" in inv` — `inv` is the campaign's declared
  invariants (read from .rumpun/rumpun.yaml by the existing load at
  lint.py:256), so campaigns without the invariant are unaffected.
- Fires when NO pipeline phase has a non-empty `reads`; message names the
  season id: "falsify_required: season sN carries no phase whose reads
  names an artifact — nothing could disconfirm its verdict; give a phase
  (typically evaluate) a non-empty reads".
- `reads` accepted as str or list, same handling as _dag_edges.
- Errors block start (existing lint severity semantics, unchanged).

## Verification (all measured this session; raw logs in results/)

| Check | Result |
|---|---|
| baseline suite (repo src, repo tests path) | 161 passed, 60.7s |
| patched suite (probe: workspace src) | 152 passed, 9 failed, 65.0s |
| sweep: 36 musim yamls, baseline vs patched findings | byte-identical (probe-filtered diff empty) |
| sweep baseline findings | s1-s34 clean (s2 warnings only); _template.yaml and s35.yaml carry pre-existing baseline errors (unfilled stubs) |
| repro C1 (invariant declared + no-read season) | exactly one error, names s40, contains falsify_required |
| repro C2/C2b (lean season, reads str / list) | zero findings |
| repro C3 (campaign without the invariant) | new error absent; only the pre-existing declaration error remains |
| repro C5 (real musim/s34.yaml, patched) | zero errors |
| ruff --no-respect-gitignore (lint.py + 3 scratch files) | clean |

Nuance 1 — "every musim/*.yaml still lints": patched findings are
byte-identical to baseline for all 36 files. _template.yaml (4 errors) and
s35.yaml (4 errors: missing primary_change fields) already errored at
baseline; they are unfilled stubs (s35 is next season's seed), pre-existing,
not caused by the patch. s2 has two warnings, also pre-existing.

Nuance 2 — C3 semantics: the pre-existing REQUIRED_INVARIANTS check
(lint.py:264-267) errors on any campaign missing a declared invariant, so a
campaign without falsify_required can never lint fully clean. C3 proves the
narrower claim the spec asks for: the new enforcement is config-gated
(the new error is absent; only the declaration error remains).

## Reproduce (absolute paths; shell cwd resets between calls)

```
V=/mnt/data/work/rumpun/.venv/bin/python
W=/mnt/data/work/rumpun/.rumpun/rimba/s34/w1
$V $W/scratch/repro_falsify.py
PYTHONDONTWRITEBYTECODE=1 $V $W/scratch/run_suite_patched.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/mnt/data/work/rumpun/src $V $W/scratch/sweep_musim.py > $W/results/sweep_baseline.txt
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$W/src $V $W/scratch/sweep_musim.py > $W/results/sweep_patched.txt
diff <(grep -v '^probe ' $W/results/sweep_baseline.txt) <(grep -v '^probe ' $W/results/sweep_patched.txt) && echo SWEEP-IDENTICAL
/home/sani/.local/bin/ruff check --no-respect-gitignore $W/src/rumpun/lint.py \
  $W/scratch/repro_falsify.py $W/scratch/run_suite_patched.py $W/scratch/sweep_musim.py
```

## For w2 and the harness

The 9 patched-suite failures all fire the new error on the tests' shared
minimal season fixture (a no-reading-phase season s1 under a campaign
declaring all three invariants). Full output: results/suite_patched.txt and
results/fail_detail.txt. Failing tests:

- test_lint_accepts_contained_benih_name[w1] / [alpha-1] / [w2_x]
- test_lint_citation_matching_digest_resolves
- test_lint_citation_8char_prefix_resolves
- test_apply_passes_clean_season_without_reject_record
- test_band_guard_warns_once_naming_sid
- test_band_guard_silent_on_compliant_band
- test_band_guard_silent_on_other_metric

Minimal fixture fix: give the shared season fixture builder's evaluate node
`reads: results.jsonl` (the lean-pipeline shape; the enforcement then stays
silent), or assert the new error where a no-read season is intended. The
test_apply path fails at evolve.apply, which surfaces lint errors verbatim.
