# s34 w2 notes — spec-first pins for the falsify_required enforcement

## Verdict

Five pins: two red against current code for the spec reasons, three
green-guards (vacuous pre-merge). Real-repo suite: 161/161 green, exit 0.
Scratch suite (166 = 161 + 5 pins) against current code: 2 failed (the red
pins), 164 passed, 0 skipped. Reference-implementation check: all 5 pins
green; the 166-item scratch suite under a reference enforcement patched into
the SCRATCH copy of lint.py fails exactly the 11 pre-existing items predicted
by the static blast map. Ruff clean. Real src/ and tests/ untouched by w2;
the scratch src patch is measurement-only.

## Measured red set (git 56c5217ed8e9bd49320c1dedf401602867dcc06c, 2026-09-15)

| pin | test | spec | measured reason |
|---|---|---|---|
| 1 | test_falsify_required_errors_on_zero_reading_phases | zero reading phases under a falsify_required campaign -> lint error naming the season | RED: "lint accepted a season with zero reading phases under falsify_required: []" |
| 2 | test_falsify_required_empty_reads_names_no_artifact | reads: [] names no artifact, cannot satisfy | RED: "an empty reads list named no artifact yet lint accepted the season: []" |
| 3 | test_falsify_required_lean_pipeline_passes | execute -> evaluate reading results.jsonl passes with zero errors | GREEN-guard: vacuous today; guards the negative case post-merge (catches over-trigger, e.g. demanding a falsify primitive) |
| 4 | test_falsify_required_any_phase_reading_an_artifact_passes | rank_gaps reading results.jsonl satisfies ("or any phase") | GREEN-guard: vacuous today |
| 5 | test_falsify_required_scope_campaign_without_invariant | bare invariants list -> no error naming the season | GREEN-guard: today only the pre-existing required-invariants error, which names the campaign, never s9 |

Red run: `2 failed, 3 passed, 161 deselected` (evidence/red-run.txt, exit 1).
Both reds fail with findings == [] — lint accepts the violating seasons
outright, the exact spec gap the akar records describe.

## Season-level finding: post-merge blast radius (measured, not projected)

The s34 expected_band demands the suite green at 161+ post-merge, but a
faithful enforcement flips 11 pre-existing test items: their fixtures carry
zero reading phases while every campaign fixture declares falsify_required.
Measured by running the 166-item scratch suite against a reference
enforcement (scratch lint.py only):

`11 failed, 155 passed, 0 skipped` (evidence/sim-full-suite.txt, exit 1):

- test_dual_start_single_spawner — `season start` preflight blocks SEASON_DUAL
- test_season_all_agents_failed_maps_to_nonzero — same preflight path
- test_apply_passes_clean_season_without_reject_record — evolve.apply lint gate
- test_lint_accepts_contained_benih_name x3 — asserts errors == [] on SEASON_S1
- test_lint_citation_matching_digest_resolves,
  test_lint_citation_8char_prefix_resolves — same on SEASON_S1 fixtures
- test_band_guard_warns_once_naming_sid,
  test_band_guard_silent_on_compliant_band,
  test_band_guard_silent_on_other_metric — helper asserts errors == [];
  BAND_GUARD_SEASON's evaluate carries no reads

The static map (call-site reading) predicted 10 of these 11; the preflight
casualty test_season_all_agents_failed_maps_to_nonzero surfaced only in the
measured run. Reconciliation is not w2's call (additions-only) nor w1's
(tests/ barred): the merger must add a reading phase to the four fixture
templates (SEASON_S1, SEASON_DUAL, BAND_GUARD_SEASON, RUMPUN_YAML_FAIL
users reaching lint via evolve.apply or season start), or the operator waives
the affected items for s34. The suite-green clause of the band cannot hold
without one of those.

## Contract the pins carry (for w1)

- Trigger: "falsify_required" in the campaign rumpun.yaml
  autonomy.invariants (the same load lint already does for REQUIRED_INVARIANTS).
- Requirement: at least one pipeline node whose reads names an artifact —
  any phase, any artifact; truthiness of reads (an empty list does not
  satisfy, pin 2).
- Finding severity: error; the message names the season id (pins assert the
  id substring in the message).
- REQUIRED_INVARIANTS is w1's freedom: pin 5 passes whether or not
  falsify_required is relaxed out of the required set (bare list then lints
  with zero errors instead of one campaign-naming error).
- Placement inside lint() is w1's freedom; pins see outcomes only.

## Green gates

- Real repo suite: 161 passed, exit 0 (evidence/suite-real-repo.txt).
- Scratch suite, current code (161 + 5 pins): 2 failed (the red pins),
  164 passed, 0 skipped, exit 1 (evidence/full-suite-current.txt).
- Reference-enforcement sim: pins 5/5 green, exit 0
  (evidence/sim-pins-green.txt); full suite 11 failed / 155 passed /
  0 skipped, exit 1 (evidence/sim-full-suite.txt).
- Ruff (line-length 100, --no-respect-gitignore): scratch test file and
  reference lint.py both "All checks passed", exit 0 (evidence/ruff-run.txt).
- Interpreter probes (evidence/interpreter-probe.txt): the repo venv imports
  rumpun from real src by default, so the red runs measured current bytes;
  PYTHONPATH=<scratch>/repo/src wins for the sim runs, so the reference
  bytes were the ones under test.
- Scratch grafts (per the s33 recipe): DESIGN.md, tools/,
  .rumpun/akar/evidence, .rumpun/rimba/s15/{w1,w2}/agent.log. The .rumpun
  graft flips _repo_root() to the scratch tree; without the s15 stream graft
  the two real-stream tests SKIP (observed once: 2 skipped in an
  intermediate run; after the graft they pass, 0 skipped in the definitive
  runs).

## Deliverables (all under w2/)

- scratch/repo/tests/test_rumpun.py — the 161 existing tests byte-identical
  prefix (cmp at 202667 bytes; original sha256 dc99709441a30b92f2bb64aba1323e
  9a6cf30f523c51934944e27c2b537c0d1a), then the s34 w2 pins section (221
  lines, 5 tests; exact appended bytes = evidence/pins-section.py, cmp
  suffix identical). 209468 bytes total, sha256 f3505abf91e8277307e2d217926d
  51a618809b72cf6a5dab7fdde083623399ff, 166 collected.
- scratch/repo/src/rumpun/lint.py — reference enforcement, measurement-only,
  never shipped; real src/rumpun/lint.py sha256 b9c9b776cb4d68427ac5a50395c
  7bcaa4f943c22a34f36cec68d75dae7ff1e23 (untouched).
- Evidence: scratch/evidence/{suite-real-repo,red-run,full-suite-current,
  sim-pins-green,sim-full-suite,interpreter-probe,ruff-run}.txt and
  pins-section.py.
- 5 new tests, 166 collected in the scratch suite; the real repo's tests/
  directory is untouched (additions land via the harness merge).

## Protocol note

Two consecutive corrupted Writes this session while authoring the pins
section (token substitutions, foreign tokens, duplicated blocks), caught on
readback both times; the chunked-heredoc fallback with per-chunk grep gates
produced byte-clean output (recorded in memory: verify-state-writes,
instances 12-13). One process slip: two background suite runs overlapped
once; both were re-run cleanly afterwards and only the definitive runs above
are cited as evidence.

## Provenance

- git HEAD 56c5217ed8e9bd49320c1dedf401602867dcc06c ("feat: s33 lands
  decadal audit; s34 seeded"); measured 2026-09-15.
- akar inputs read: audit-23 (sha256 f76fcace...ba74a) and
  usefulness-decade-3 (sha256 3d4d28d7...857b), both cited in musim/s34.yaml.
- Working-tree note: campaign runtime artifacts at repo root (logs/*,
  replay-matrix.md) show as modified from season traffic including this
  session's real-repo suite run; .rumpun/musim/s35.yaml is the harness's
  next-season seed. w2 wrote only inside w2/.
