# s47 w1 notes — the plugin machinery's completion

Deliverables landed in workspace copies `src/rumpun/plugin.py` +
`src/rumpun/cli.py` (full src tree copied; the merger grafts the two).

## What landed

plugin.py:

- `resolve_prompt(root, rel) -> Path | None` replaces `resolve_template`
  (no alias kept: the deliverable keeps one only if init_project still
  calls it; after the rewrite nothing does, and grep shows no other
  caller in src/ or tests/). root is the campaign `.rumpun` dir; packs
  sit at `root/plugins/<name>/`, tried in sorted-name order, first
  `priors/<rel>` hit wins, fallback `root/<rel>`, None if nowhere.
  Covers pins 5/5b.
- Manifest gates: the s46w2 fixture field set (name, version, digest,
  private_vocabulary, source) was already accepted; the reconciled part
  is what `digest` MEANS. `priors_digest(pack_dir)` now hashes the
  pinned convention: sorted pack-relative POSIX paths (priors/ prefix
  included), update(rel), update(NUL), update(bytes), no trailing NUL.
  The old priors-relative trailing-NUL form had no pins of its own
  (s44 fixtures use placeholder digests), so it was replaced outright.
  Covers pins 1-3.
- `plugins_dir(root)` = `<root>/.rumpun/plugins` (was `<root>/plugins`).
- `plugin_install` stages manifest.yaml beside priors/, so the installed
  manifest doubles as the pinned install record (name/version/digest
  under `.rumpun/plugins/<name>/`, outside priors/). The plugins.yml
  registry row stays as secondary metadata. campaign/ never installs
  (discover_priors walk, unchanged). Pins 1, 2, 6.
- `init_project(plugins)`: `--plugin` now names a PACK DIRECTORY. Each
  pack installs into the target first (digest-verified, lint-gated,
  priors/ only), the scaffold resolves pack-first via resolve_prompt,
  and an empty goal/metric in seasons/s1.yaml is seeded from the first
  pack's name so the scaffolded campaign lints clean (pin 4; w2's
  finding 2). Overwrite guard runs before any install or write.

cli.py:

- `_setup_logging` adds `force=True`. Without it basicConfig is a no-op
  under pytest (caplog already holds a root handler), so install
  refusals never reached stderr and pin 2 could not see the pack name.
  Grep evidence: no suite test asserts caplog content from a cli.main
  call, so nothing depended on the no-op.
- `--plugin` metavar/help now say PACKDIR; cmd_init comment updated.
- PluginError -> exit 1 was already in main()'s except tuple (s46 w1
  landed it); w2's finding 1 was already resolved on main.

## Measured (this workspace)

Interpreter: repo `.venv`, `PYTHONPATH=<ws>/src`; probe_w1.py confirms
plugin and cli import from `<ws>/src` (the editable .pth appends after
PYTHONPATH, so the workspace wins).

- w2 pins: 7/7 passed (log_pins.txt). The same file measured 7/7 FAILED
  against the unpatched repo tree (log_suite_baseline.txt).
- Full suite, patched tree: 217 passed, 4 failed (log_suite.txt).
  Baseline, unpatched repo tree, no PYTHONPATH: 210 passed, 11 failed
  (log_suite_baseline.txt). Delta = exactly the 7 s46 pins; zero new
  reds.
- The 4 remaining reds are pre-existing and out of w1 scope:
  - 3 x test_s43_w2_pins coverage pins (fresh-matrix coverage finding
    missing) — they also fail solo (log_s43_solo.txt: 3 failed, 5
    passed).
  - test_s38_coldstart_checker_leaves_repo_rumpun_untouched — fails in
    BOTH full-suite runs (baseline and patched), identically; passes
    outside the full order. Deterministic repo-state red: the repo's
    .rumpun carries untracked drift (e.g. seasons/s48.yaml, mtime
    20:24) that the coldstart checker reports as "added". Suite-order
    or repo-state dependent, pre-existing.
- ruff: both files clean, --no-respect-gitignore (log_ruff.txt).

## Concurrent-edit caveat (merger: read before grafting)

w2 edited tests/test_rumpun.py at 20:52:50 today (git diff vs HEAD:
_write_proj now also creates ledger/ and runs/; the two GOLDEN audit
bodies re-captured "post-s45", "musim" scope strings renamed; header
comments say "Re-captured 2026-09-15 (s47/w2)"). My two full-suite runs
straddle that save; collection timing decides which file version each
run saw. The edit touches neither the s38 coldstart test nor the s43
coverage pins, so the 4 pre-existing reds are unaffected by it. w2 owns
tests/; I did not touch it.

## Post-patch fixes the readback caught

- The generated --plugin help line lost its closing quote and paren
  (patch-script string concat bug); sed-restored, grep shows the
  balanced line at cli.py:487.
- patch_w1.py's logger crashed after the plugin.py write
  (Path.write_bytes returns a count, not the data); the re-run skipped
  plugin.py on gone anchors (logged) and applied cli.py. Both full
  diffs vs the repo copies reviewed hunk by hunk (log_diff_plugin.txt,
  log_diff_cli.txt).

## Post-graft expectation (for the merger)

With both files grafted: the s46 pins file goes 7/7 green; expect 217
passed plus the same 4 pre-existing reds (221 collected today) until
the s43 coverage pins and the s38 coldstart state issue are addressed
by their owners.

## Artifacts

patch_w1.py, probe_w1.py, patch.log, log_pins.txt, log_suite.txt,
log_suite_baseline.txt, log_s43_solo.txt, log_ruff.txt,
log_diff_plugin.txt, log_diff_cli.txt.
