# s36 w1 — stall-resume logic in evolve draft_next

## Verdict

DONE. draft_next now resumes a stopped_stall parent: every benih budget
raises to its times 1.5 (rounded up to whole minutes) and the yaml header
gains the stall citation line. Non-stall parents draft byte-identical to
the pre-s36 behavior.

✅ VERIFIED REAL: every claim below rests on a captured run under
`scratch/evidence/`.

## What changed — src/rumpun/evolve.py only

- `_stall_resume(root, parent, parent_id)`: reads the parent's persisted
  engine state with engine.read_persisted_status on the parent sid.
  Terminal stopped_stall returns the resume map. No persisted state (season
  applied but never started) logs info and returns None. Any other status
  (running, completed, stopped_operator, failed, stopped_budget) returns
  None. Logged, never silent.
- `_stall_budgets(parent, parent_id)`: builds the parent-minutes -> raised
  map, math.ceil(minutes * 1.5). Malformed benih or budgets on a stalled
  parent raise EvolveError (refuse to draft, no silent partial resume).
- `_render(..., resume=None)`: with a resume map the header gains
  `# resumed from stopped_stall parent <sid>; budget <old> -> <new> min`
  and every benih `budget: {minutes: N}` line is rewritten to its raised
  value. resume=None keeps the historical byte path. The stop block
  (`{stall_minutes: 15}`) is untouched.
- `draft_next` computes the resume map after the existing validations and
  passes it to _render. Module and draft_next docstrings updated.

Patch readback: `diff <real evolve.py> <scratch evolve.py>` shows exactly
the intended hunks (`evidence/diff-vs-real.txt`). Patched file sha256:
849c31c34aa35257b02679629fc6af22d6df1d02ac7945a2f23fb5b7cfa1a83b

## Contract details for w2's pins

- Header line, exact: `# resumed from stopped_stall parent <parent sid>; budget <old> -> <new> min`.
  Uniform budgets give one pair; distinct values give comma-joined pairs in
  benih order (dedup by old value).
- Rounding: math.ceil of minutes * 1.5. 40 -> 60, 33 -> 50.
- Only lines matching `^(\s*)budget: \{minutes: (\d+)\}$` rewrite (the only
  budget format anywhere in musim/). The stop block is untouched.
- Gate: only terminal status stopped_stall triggers. `running` does not.
- No persisted engine state for the parent (applied, never started): info
  log, draft proceeds verbatim.
- A stalled parent with missing/malformed benih budgets raises EvolveError
  instead of drafting. Such a parent never passed apply, so refuse-to-draft
  is the honest path.
- A budget line in text whose value is absent from the parsed benih map
  raises EvolveError (text/parse drift guard).

## Evidence — all under scratch/evidence/

| gate | result | file |
|---|---|---|
| suite @ HEAD, real src | 171 passed, exit 0 | suite-real-repo-head.txt |
| suite, scratch src unpatched | 171 passed, exit 0 | suite-real-repo-scratchsrc-unpatched.txt |
| repro, pre-patch | 6 stall checks FAIL in-spec, byte-identity checks PASS, exit 1 | repro-run-prepatch.txt |
| repro, patched | 10/10 checks PASS, exit 0 | repro-run-patched.txt |
| suite, patched, SOLO | 171 passed, exit 0 | suite-real-repo-scratchsrc-patched-solo.txt |
| suite, patched, first run | 170 passed, 1 failed, exit 1 | suite-real-repo-scratchsrc-patched.txt |
| ruff --no-respect-gitignore, whole src/ | all checks passed, exit 0 | ruff-run.txt |
| interpreter probes, both trees | exit 0 both | probe-real-src.txt, probe-scratch-src.txt |
| patch readback diff | intended hunks only | diff-vs-real.txt |

The first patched-suite run failed `test_stop_racing_spawn_tracks_and_kills_every_spawn`
(tests/test_rumpun.py:1840, engine H1 spawn-race pin; zero evolve/draft
references in its body) while the repro ran concurrently on this box. Solo
re-run: 171 passed. The signature matches the documented load flake for
that pin, so the failure is judged load-induced, not a patch effect. Both
runs are recorded above.

## Repro design (scratch/repros/draft_resume_repro.py)

Baseline module (real repo src) and patched module (scratch src) are loaded
side by side (fresh rumpun import per tree) and draft from identical
fixture roots:

1. stopped_stall, budgets 40/40 -> citation line exact, budgets 60/60,
   every other byte equal to the baseline draft.
2. stopped_stall, budgets 40/33 -> 60/50 (ceil), header pairs in benih
   order.
3. completed parent -> byte-identical to baseline (sha equal).
4. stopped_operator parent -> byte-identical.
5. no persisted engine state -> byte-identical.

Case 1 and 2 also pin: yamlio round-trip parses the draft, id s2 parent s1,
approach line carried, stop block verbatim.

## Method

- Interpreter: /mnt/data/work/rumpun/.venv/bin/python (pytest 9.1.1,
  Python 3.13.12). ruff 0.14.10.
- The suite runs from the real repo tests/ with PYTHONPATH=<scratch>/src;
  the suite is not copied and .venv is not copied. The editable-install
  .pth is shadowed by PYTHONPATH, probed in both directions.
- ruff runs inside scratch/repo so the pyproject line-length 100 applies,
  with --no-respect-gitignore (rimba/ trees are gitignored).

## Merge note

Take `scratch/repo/src/rumpun/evolve.py` wholesale (sha256 above); no other
repo file changed. w2's pins merge on top; the harness owns the tree.
