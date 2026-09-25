# s35 w1 — verdict-versus-artifact cross-check in run_audit

## What landed
- Patched merge source: `scratch/src/rumpun/audit.py` (full package copy of repo `src/rumpun`).
- New deterministic trigger in `_findings_and_candidates`: an engine season whose
  last season-level verdicts.jsonl row says WIN while its results.jsonl carries a
  row with `verdict` FAIL arms ONE candidate per mismatching season:
  `candidate: verdict mismatch: <sid> harvested WIN while its results carry FAIL (<unit>); band: WIN when the verdict matches the artifacts`
- Module docstring trigger list gained the rule (after recalibrate, before stall).
- F5 loop now captures rows into a `result_rows` dict; counts and lines unchanged.

## Design decisions
- Scope: engine seasons holding results.jsonl (the `harvested` list F5 already
  computes). Season verdict via existing `_season_verdict` (last season-level
  row, report rule [H]). No season verdict, or a non-WIN verdict, arms nothing.
- "results rows with verdict fields": only `row.get("verdict") == "FAIL"` counts;
  verdict-less rows are not statements (`_read_jsonl` convention).
- One candidate per mismatching season even with several FAIL rows. The unit
  named is the first FAIL row in file order (`corpus_fails[0]` precedent).
  Missing/empty `unit` renders `?` (route `?` precedent).
- Placement: after the calibration proposal, before stall — same band-consistency
  family; stall stays last among the deterministic season triggers.
- No new finding line: the spec defines only the candidate; usefulness-residual
  precedent covers a candidate without a dedicated F line. Evidence cited
  in-line via `<sid>`.

## Evidence (✅ measured this session)
- Write gate: `diff -u` repo `audit.py` vs patched copy shows exactly 3 hunks
  (docstring bullet, F5 row capture, trigger loop). Nothing else.
- Repro: `scratch/repro/repro.py` under both sources; every record copy embeds
  the resolved `rumpun.audit` path (resolution probe). Base resolved to repo src,
  patched to scratch src.
  - mismatch fixture (s1 WIN + FAIL rows u_mid,u_last; s2 WIN consistent): base
    says `candidates: none`; patched carries exactly
    `candidate: verdict mismatch: s1 harvested WIN while its results carry FAIL (u_mid); band: WIN when the verdict matches the artifacts`
    — unit = first FAIL in file order; that line + sha256 are the only changes.
  - consistent fixture (WIN all-WIN results + masked LOSS): record byte-identical
    to base (equal sha256), arms nothing.
  - noresults fixture (WIN verdict, no results.jsonl; second season FAIL results
    without season verdict): byte-identical, unaffected.
  - ordering fixture (mismatch s1 + masked-LOSS s2,s3, all stopped_stall): exactly
    3 candidates in order calibration, mismatch, stall — joins the proposals
    before the cap.
  - F3 line identical in all four fixtures (grep-diff).
- ruff: `ruff check --no-respect-gitignore` on the patched file: All checks passed.
  (venv has no ruff; used `~/.local/bin/ruff`.)
- Suite: ✅ `166 passed in 55.98s` against `PYTHONPATH=$W/scratch/src`
  (repo tests, venv python, log at scratch/suite.log, exit 0).

## Repro commands (exact)
```
W=/mnt/data/work/rumpun/.rumpun/rimba/s35/w1
cd /mnt/data/work/rumpun
PYTHONPATH=/mnt/data/work/rumpun/src .venv/bin/python $W/scratch/repro/repro.py $W/scratch/repro/work-base $W/scratch/repro/out/base
PYTHONPATH=$W/scratch/src .venv/bin/python $W/scratch/repro/repro.py $W/scratch/repro/work-patched $W/scratch/repro/out/patched
diff -r $W/scratch/repro/out/base $W/scratch/repro/out/patched
PYTHONPATH=$W/scratch/src .venv/bin/python -m pytest tests -q
```

## For w2 (pins)
- No existing fixture contains a results row with `verdict: "FAIL"` (grep over
  tests/test_rumpun.py: all FAIL hits are corpus-matrix rows), so the new trigger
  cannot fire in existing pins.
- Fixture recipe: `_write_harvest_record(root, sid, "WIN")` for the season row,
  `_write_results_rows(root, sid, [{"unit": ..., "verdict": "FAIL", ...}])` for
  the mismatch; the trigger needs a rimba/<sid> dir and the season in the window.
- Pin the order expectation too: calibration < mismatch < stall.

## Files touched (workspace only)
- `scratch/src/rumpun/audit.py` — the patched merge source.
- `scratch/repro/repro.py`, `scratch/repro/out/{base,patched}/`, logs.
- `notes.md`. No file outside this workspace written; collab.py, engine.py,
  harvest.py, evolve.py, lint.py, cli.py, report.py, tools/, tests/ untouched.
