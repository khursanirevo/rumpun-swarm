# s51 w2 — spec-first pins for the extended distill

## Shipped
- tests/test_s51_w2_pins.py (343 lines, 3 tests, additions-only: a new
  file; no existing suite file touched).
- Ruff clean (`--no-respect-gitignore`; repo pyproject rules: E,F,I,UP,B,
  SIM,RUF; line-length 100).

## Spec reconciled
- seasons/s51.yaml expected_band: WIN if "distill emits evidenced
  patterns and templates inside priors/ (priors/patterns/,
  priors/templates/), generalized (no sids, campaign names, or absolute
  paths), self-lint clean, digest verified over the full priors/ tree,
  install round-trip green, and the suite holds its floor (the four
  known reds stay the only reds)"; LOSS otherwise.
- The band's baseline names the campaign's four working patterns
  (spec-first pinning, merge reconciliation, harvest close, the replay
  corpus gate) and four reusable templates (season yaml, harvest note,
  pins header, the akar record shape) — these are the classes the pins
  require, as any-of stem groups over filenames plus text.
- plugin.py (landed s44/s46/s50): plugin_lint, priors_digest,
  plugin_install, plugin_list, SID_TOKEN_RE, ABS_PATH_RE, WIN_PATH_RE,
  DIGEST_RE, TERM_RE, and the s50 plugin_distill (evidence-gated gate
  selection from DESIGN.md + .rumpun/ledger/*.md, digest sealed over the
  staged priors/ tree, self-lint refuses on error). The extension adds
  the priors/patterns/ + priors/templates/ emission; the pins declare
  that interface for w1 (reconcile at graft, as in s46/s50).
- akar audit-38: WIN 32 / LOSS 1 / INVALID 0 of 32 engine verdicts;
  corpus fresh matrix, 5 PASS / 0 FAIL / 0 DRIFT, all green on main, no
  candidates. akar s50-harvest: WIN — the export side proven, the
  s51 extension is its second half.
- Campaign name surface: unchanged from s50 — .rumpun/rumpun.yaml
  carries no campaign name field; the campaign root dir name "rumpun"
  is the only ban token beyond sids and absolute paths.

## Pins (tests/test_s51_w2_pins.py)
1. test_s51w2_distill_emits_patterns_and_templates — `plugin distill
   kaggle-base --source <note>` (subprocess, 120s bound) exits 0; the
   draft exists at .rumpun/plugins/kaggle-base-draft/; manifest loads
   with name kaggle-base, version 0.1.0; the s50 gates stay (top-level
   priors/ files carry the four gate stems falsif/band/stall/drift);
   priors/patterns/ and priors/templates/ are non-empty and cover the
   band's four pattern stems (spec, merge, harvest, replay-or-corpus)
   and four template stems (season, harvest, pin, akar-or-record);
   plugin_lint reports zero errors on the emitted pack (self-lint
   clean; unknown manifest keys are lint violations, so a lint-clean
   manifest is the unchanged-s44-schema proof).
2. test_s51w2_new_classes_carry_no_campaign_privates — the s50 pin-2
   shape applied to the new classes: no sid token (SID_TOKEN_RE), no
   absolute-path token (ABS_PATH_RE / WIN_PATH_RE), no campaign name
   token (\\brumpun\\b) in any patterns/ or templates/ filename or
   content line.
3. test_s51w2_full_tree_digest_and_install_round_trip — the manifest
   digest equals an independent sha256 recomputation over the FULL
   priors/ tree and plugin.priors_digest; `plugin install` on the draft
   exits 0; plugins/kaggle-base/ holds manifest.yaml plus the draft's
   exact priors/ rel set including priors/patterns/ and
   priors/templates/ files; plugins.yml (via plugin.plugin_list)
   records kaggle-base with the pack digest; the installed manifest's
   digest verifies over the installed tree.
4. Regression duty is out-of-band (s30 pin-5 precedent: no test runs
   the suite from inside itself); see Regression below.

## Spec tension (recorded for the merge)
- Stem naming: the pattern/template stem groups are any-of
  ("replay", "corpus") and ("akar", "record") where w1's generalized
  wording could differ. A miss fails legibly with the missing group
  named; widening a stem group at graft is w1's call.
- Pin 3's digest clause verifies over the whole existing tree, so it
  holds today (gates-only) and the red lands on the missing classes;
  once w1's emission lands, the same assertion pins the full tree.

## Regression (measured, main @ be60697 + w1's in-flight s51 edit)
- Baseline suite (launched before any w2 write, 664.34s, log
  /tmp/s51w2-suite-baseline.log): **4 failed, 220 passed, 3 errors**.
- The four FAILED are the four known reds, unchanged from s50's
  measured baseline:
  - test_rumpun.py::test_s38_coldstart_checker_leaves_repo_rumpun_untouched
  - test_s43_w2_pins.py::test_fresh_matrix_coverage_finding_counts_all_rows
  - test_s43_w2_pins.py::test_coverage_gap_is_finding_never_candidate
  - test_s43_w2_pins.py::test_coverage_zero_pass_is_honest
- The 3 ERRORS are NOT regressions from s51 w2 work: the baseline
  suite raced w1's in-flight edit of src/rumpun/plugin.py — the s50
  pins fixture's `rumpun init` subprocess imported a broken
  intermediate (SyntaxError at plugin.py:969, "if any(pattern.search(
  corpus) over prior.evidence):"; git diff at measurement time +151/-9
  uncommitted). My own pins run and the co-collection ran in a valid
  window and imported a parsing plugin.py.
- Floor certification is therefore split: the four known reds stand as
  the only FAILED set; the s50 pins module needs one clean re-run once
  w1's edit parses (pending at w2 budget end).
- The suite run dirties tracked logs/*.out and replay-matrix.md (and
  .rumpun/RESUME.md) per the repro-adapter side effects; documented,
  not a new s51 effect.

## Measured red set (main @ be60697, pytest 9.1.1)
- Run: `.venv/bin/python -m pytest .rumpun/runs/s51/w2/tests/
  test_s51_w2_pins.py -q` → **3 failed in 3.64s**, rc 1. All three fail
  at the patterns-presence assertion — "AssertionError: no
  priors/patterns/ content: the extension is missing" (lines 250/278/
  322). The intended spec reason: the s50 distill exists and emits the
  four gates only; priors/patterns/ and priors/templates/ are never
  created. The fixture's init and distill subprocesses passed before
  the failing assertions (distill rc 0), so no earlier step is masked;
  pin 3's digest clause (independent recompute + priors_digest
  cross-check) passed before its red point, over the current gates-only
  tree.
- Ruff: `ruff check --no-respect-gitignore` on the pins file → all
  checks passed (repo pyproject rules, line-length 100).
- Co-collection: `pytest tests/ <pins file> --collect-only -q` → 230
  collected (227 existing + 3 new), rc 0, no collection errors — the
  graft is additions-only.

## Handoff
- w1 lands the patterns + templates emission in plugin_distill
  (evidence-gated selection from the ratified records, fixed generalized
  bodies, digest over the full staged tree, self-lint as in s50); the
  three pins then go green at merge, and the regression section's split
  floor note resolves with one clean s50-module re-run once w1's edit
  parses.
