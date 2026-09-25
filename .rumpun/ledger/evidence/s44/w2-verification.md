# s44 w2 notes — plugin-boundary pins + kaggle-base seed draft
date: 2026-09-15
lane: plugin-pins (fable, 40-minute budget)

## Measured red set

- Pins: tests/test_s44_w2_plugin_pins.py, 6 test functions = 8 tests.
- vs repo main: 8/8 red at collection — ImportError (no rumpun.plugin on
  main), exit 2 (log_pinsred.txt). Intended red: the boundary does not
  exist on main.
- vs w1's landed src/rumpun/plugin.py: first contact 3/8 passed, 5 failed
  on fixture deltas; after reconciliation 8/8 passed, exit 0
  (log_pins_vs_w1.txt).
## Repo baseline at HEAD (pre-existing; not caused by s44 work)

- 196 collected. Full-suite runs: 192 passed / 4 failed, consistent across
  two full reruns:
  - tests/test_rumpun.py::test_s38_coldstart_checker_leaves_repo_rumpun_untouched
  - tests/test_s43_w2_pins.py::test_fresh_matrix_coverage_finding_counts_all_rows
  - tests/test_s43_w2_pins.py::test_coverage_gap_is_finding_never_candidate
  - tests/test_s43_w2_pins.py::test_coverage_zero_pass_is_honest
- The s43 record ("suite 188/188 at landing") does not reproduce at HEAD
  in this environment; 3 of its 8 pins are red on main.
- The first run's 5th failure passed on both reruns (flake; name uncaptured).
- During this session an untracked .rumpun/musim/s46.yaml appeared in the
  repo (not my write; origin unknown; flagged for the operator).
## Interface reconciliation (pins adapted to w1's landed module)

- plugin_lint requires manifest.yaml on disk inside the pack: the pack
  helper now writes it from the manifest dict.
- private_vocabulary must be non-empty (strict v1 schema): fixtures carry
  one term ("sampleterm").
- Installer discovery is discover_priors(pack_dir) -> sorted full Path
  list; pin 5 uses the landed name and normalizes to pack-relative paths.
## Seed draft review

- Mechanical: scripts/seed_check.py — leak tokens, sid and absolute-path
  regexes, yaml parse, Generalized-from tail rule: clean, exit 0. ruff
  clean.
- Prose: all four files read end-to-end; they read as general knowledge:
  no project sids, names, or absolute paths; each ends with its
  generalization source noted as a pattern.
- Files: patterns/the-falsify-gate.md, patterns/the-band-mask-guard.md,
  patterns/stall-resume.md, seasons/a-season-template.yaml.
## Artifacts

- tests/test_s44_w2_plugin_pins.py (225 lines, 6 test functions = 8 tests)
- seed/kaggle-base/: 3 patterns + 1 season template
- scripts/seed_check.py (75 lines)
- log_fullsuite.txt, log_pinsred.txt, log_pins_vs_w1.txt

## Sources

- akar/directives.jsonl seq 2 (plugin/hub directive, pending)
- akar record audit-33 (sha256 8e2939b38aceb14988b8fca4bfb29c54e5f265ce66aeb6e97af4af43dc218359)
- DESIGN.md section 16: the s32 band-mask, s34 falsify-gate, and s36
  stall-resume rows (the arc's proven gates, per the season method)
