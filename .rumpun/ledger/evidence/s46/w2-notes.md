# s46 w2 — spec-first pins for plugin install/list/use

Deliverable: `tests/test_s46_w2_plugin_pins.py` (7 pins, additions-only,
graft into `tests/` as-is). Measured red against current code; the
pre-existing suite is untouched.

## Spec sources (read)

- `musim/s46.yaml` — the WIN band, quoted in the pins docstring.
- akar `audit-34` @ `4f9d23f9` — reflection audit; F3 histogram, fresh
  matrix 5 PASS / 1 DRIFT; no install-arc blockers.
- akar `s44-harvest` @ `e585de8e` — WIN; the boundary shipped module-level;
  "the hub formats and distill follow."
- `src/rumpun/plugin.py` (s44 landed) — pack format, `plugin_lint`,
  `discover_priors`; campaign/ structurally invisible to discovery.

## Pinned interface (declared for w1; reconcile at graft, as in s44)

- CLI: `rumpun plugin install <pack-dir>` / `rumpun plugin list` from a
  campaign root; `rumpun init <target> --plugin <pack-dir>`.
  Install refusal exits 1 naming the pack.
- `plugin.resolve_prompt(root, rel) -> Path`: first installed pack whose
  priors tree carries `<rel>` wins; fallback `root/<rel>`; root is the
  campaign `.rumpun` dir; packs sit at `root/plugins/<name>/priors/<rel>`.
- Digest w1 must verify: sha256 over priors/ files sorted by pack-relative
  posix path — update(rel), update(b"\0"), update(file bytes). The test
  helper computes it independently; install must match.
- Install record: a file under `.rumpun/plugins/<name>/` outside `priors/`
  naming name, version, digest.

## Two findings w1 needs (measured today)

1. `cli.main`'s except-tuple does not map `plugin.PluginError`; a refusal
   would escape as a traceback, not exit 1. w1 must add it.
2. A fresh scaffold lints DIRTY (empty goal/metric → rc 1; probe evidence
   `scratch/probe_scaffold_lint.out`, rc_lint=1). The band's repro "the
   scaffolded campaign lints clean" therefore requires `init --plugin` to
   seed goal/metric from the pack. Pin 4 holds w1 to exactly that.

## Measured red set (evidence: scratch/red-run.txt)

Suite: pytest 0.31s, 7 failed, 0 passed, rc 1. Every pin failed for the
intended spec reason; no collection errors, no fixture escapes.

| pin | test (test_s46w2_) | measured red reason |
|---|---|---|
| 1 | install_copies_priors_and_writes_record | rc 2 vs 0: `invalid choice: 'plugin'` |
| 2 | install_refuses_tampered_pack_naming_it | rc 2 vs 1: `invalid choice: 'plugin'` |
| 3 | list_shows_name_version_digest | rc 2 vs 0: install step, `invalid choice: 'plugin'` |
| 4 | init_plugin_scaffolds_and_lints_clean | rc 2 vs 0: `unrecognized arguments: --plugin` |
| 5 | prompts_resolve_pack_before_base | `AttributeError: module 'rumpun.plugin' has no attribute 'resolve_prompt'` |
| 5b | prompts_fall_back_to_base | same AttributeError as pin 5 |
| 6 | campaign_content_never_installs | rc 2 vs 0: `unrecognized arguments: --plugin` |

## Suite

- Pre-existing suite measured today: 214 collected (base `test_rumpun.py`
  188 + s43/s44/s45 pin files). Baseline run: PENDING (background).
- Post-graft expectation: 214 pass + 7 red; w1 lands the capability and
  the graft turns 7 green → 221 green.

## Environment notes for the merger

- `.venv` has no ruff; system ruff 0.14.10 works:
  `ruff check --no-respect-gitignore <file>` (the pins file passed).
- Pins file ruff: all checks passed (0 findings).
- Bash cwd resets to the workspace between calls; prefix `cd /mnt/data/work/rumpun`.
