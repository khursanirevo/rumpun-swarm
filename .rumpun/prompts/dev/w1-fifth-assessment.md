# s114 w1 — the fifth usefulness assessment

The standing assessment sealed at s97-s101 and s104 (the fourth). None
since: five seasons of closes have ridden on the auto-continue directive
alone. The fifth reads the ledger with the module.

## Ground truth (measured 2026-09-20)
- the seam: src/rumpun/audit.py usefulness_inputs and
  seal_usefulness_assessment (the s88 w2 lane); dispatched from
  src/rumpun/cli.py via harvest --assessment-file (the inputs pre-flight
  runs BEFORE any close write; a bad file refuses the whole verb)
- the basis convention: a sealed assessment's basis line is corrected by
  the supersede record (src/rumpun/audit.py line 41, the s105 w2 lane)
- the priors: the usefulness-* records in .rumpun/ledger/ (enumerate
  them FIRST; the brief lags the ledger)
- the fronts to judge: the forge merge decision table (operator), the
  second-opinion loop (ten panel verdicts, the dissent marks), the
  notes gate (one production catch), the auto-continue directive
  (directives.jsonl id 17)

## Task
1. Enumerate the usefulness-* records and the s105-s113 season rows;
   compose the assessment (objective, the continue-or-pause call, the
   basis naming what changed since s104); seal it through the module
   with --assessment-file at this season's close. The assessment yaml
   lives in the campaign; the pins cover the inputs pre-flight:
   tests/test_s114_fifth_assessment.py red-first (a bad basis, a
   missing key, the happy path).
2. Verify: the pre-flight pins green; the record sealed and readable
   back; full suite green vs the known reds (solo-run any new red);
   ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: the assessment yaml (campaign file), tests/
  test_s114_fifth_assessment.py, and src/rumpun/audit.py ONLY if the
  pin needs a seam. notes.md REQUIRED.
