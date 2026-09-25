# s50 w2 — spec-first pins for plugin distill

## Shipped
- tests/test_s50_w2_pins.py (272 lines, 3 tests, additions-only: a new
  file; no existing suite file touched).
- Ruff clean (`--no-respect-gitignore`; repo pyproject rules: E,F,I,UP,B,
  SIM,RUF; line-length 100).

## Spec reconciled
- musim/s50.yaml expected_band: "plugin distill emits a kaggle-base pack
  draft with priors/ content extracted from the campaign's proven gates
  (the falsify gate, the band-mask guard, the stall-resume pattern, the
  DRIFT retirement) AND the manifest carries the computed digest AND
  plugin lint passes on the emitted pack AND init --plugin scaffolds from
  it (repro) AND the suite is green (188+ tests)".
- w1's declared CLI: `rumpun plugin distill <pack_name> --source <note>`;
  the draft lands at .rumpun/plugins/<pack_name>-draft/ (w1 brief).
- plugin.py (landed s44/s46): plugin_lint, priors_digest, plugin_install,
  plugin_list, SID_TOKEN_RE, ABS_PATH_RE, WIN_PATH_RE, DIGEST_RE,
  TERM_RE — the pins check the emitted pack against these landed APIs.
- akar audit-38: the campaign carries 24 WIN / 1 LOSS / 0 INVALID of 32
  verdicts; corpus all green on main; no candidates. akar s44-harvest:
  WIN, the plugin/hub arc begins; s50's distill is its export side.
- Campaign name surface: .rumpun/rumpun.yaml carries no campaign name
  field; the campaign root dir name "rumpun" is the campaign's name and
  the only ban token beyond sids and absolute paths.

## Pins (tests/test_s50_w2_pins.py)
1. test_s50w2_distill_emits_lint_clean_pack — `plugin distill kaggle-base
   --source <note>` (subprocess, 120s bound) exits 0; the draft exists at
   .rumpun/plugins/kaggle-base-draft/; manifest strictly loads with
   name kaggle-base, version 0.1.0, schema-valid non-empty
   private_vocabulary, source == the note; manifest digest == an
   independent sha256 recomputation AND plugin.priors_digest; priors/
   non-empty with the four gate stems (falsif, band, stall, drift)
   present; plugin_lint reports zero errors on the emitted pack.
2. test_s50w2_distilled_priors_carry_no_campaign_privates — the
   guardrails' own rules applied to the distill's output: no sid token,
   no absolute-path token, no campaign name token in any priors filename
   or content line; plugin_lint zero errors under the emitted manifest.
3. test_s50w2_install_round_trip_lands_the_pack — `plugin install` on the
   draft exits 0; .rumpun/plugins/kaggle-base/ holds manifest.yaml plus
   the draft's exact priors/ rel-path set; plugins.yml (via
   plugin.plugin_list) records kaggle-base with the pack digest; the
   installed manifest's digest verifies over the installed tree.
4. Regression duty is out-of-band (s30 pin-5 precedent: no test runs the
   suite from inside itself); see Regression below.

## Spec tension (recorded for the merge)
- The w1 brief drafts the manifest with `private_vocabulary: []`, but the
  landed s44 lint schema requires a non-empty list, and the s50 band
  requires plugin lint to pass on the emitted pack. The pins enforce the
  band: the distill must emit a lint-clean manifest. Reconcile at merge
  (non-empty general vocabulary, or a lint rule change is w1's call).
- The band's "init --plugin scaffolds from it" clause rides the same
  plugin_install gate; the pins hold `plugin install` directly (the w2
  brief's round trip). No pin needed for init's scaffold phase.

## Regression (measured, pre-existing state of main @ 8213199)
- Baseline (clean tree, before any w2 write, pytest 9.1.1, 413.8s):
  **4 failed, 220 passed**; the four reds are NOT from s50 work:
  - test_rumpun.py::test_s38_coldstart_checker_leaves_repo_rumpun_untouched
    (AssertionError: the checker mutated the repo's own .rumpun tree)
  - test_s43_w2_pins.py::test_fresh_matrix_coverage_finding_counts_all_rows
  - test_s43_w2_pins.py::test_coverage_gap_is_finding_never_candidate
  - test_s43_w2_pins.py::test_coverage_zero_pass_is_honest
    (all three: no coverage finding in the audit text)
- The suite run also dirtied tracked logs/*.out files (repro-adapter
  side effects); the s38 red is the memory-recorded checker mutation,
  not log placement.
- Count check: 224 tests collected; test_rumpun.py holds exactly 188 —
  187 green, 1 pre-existing red (the s38 checker pin above). The band's
  "188+ tests" floor is met by the suite size, not by a green suite
  today; the four main reds predate s50.

## Measured red set (main @ 8213199, pytest 9.1.1)
- Run: `.venv/bin/python -m pytest .rumpun/runs/s50/w2/tests/
  test_s50_w2_pins.py -q` → **3 failed in 0.41s**, rc 1. All three fail
  at the distill rc assertion: argparse rejects the verb — "invalid
  choice: 'distill' (choose from install, list)" (SystemExit 2, rc 2 in
  the subprocess). The intended spec reason: `plugin distill` does not
  exist on main. The campaign fixture (rumpun init + gate-material
  overlay) passed before the failing assertion, so no earlier step is
  masked.
- Ruff: `ruff check --no-respect-gitignore` on the pins file → all
  checks passed (repo pyproject rules, line-length 100).
- Co-collection: `pytest tests/ <pins file> --collect-only -q` → 227
  collected (224 existing + 3 new), no collection errors — the graft is
  additions-only.
