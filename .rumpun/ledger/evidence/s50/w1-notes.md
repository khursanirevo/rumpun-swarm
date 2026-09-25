# s50 w1 — plugin distill: the flywheel's export

## What shipped (workspace copies; the harness merges)

- `scratch/src/rumpun/plugin.py` — appended s50 section (~297 lines):
  `DistilledPrior` frozen dataclass; `DISTILLED_PRIORS` (the four proven
  gates); `_distill_corpus(root)`; `plugin_distill(root, pack_name,
  source_note)`. No existing code touched; diff vs repo original is a pure
  append (verified by `git diff --no-index`).
- `scratch/src/rumpun/cli.py` — two hunks: `cmd_plugin_distill` (after
  `cmd_plugin_list`) and the `plugin distill <pack_name> --source <note>`
  parser wiring (after the `plugin list` parser). Diff readback shows
  exactly these two hunks and nothing else.
- `scratch/verify_distill.py` — workspace tooling: independent lint +
  digest readback of an emitted pack (physical script, logging, ruff clean).
- `scratch/repro.log` — captured repro output.

## Design

- Scan: `_distill_corpus` reads DESIGN.md plus `.rumpun/ledger/*.md`
  (sorted), then each gate's evidence patterns (case-insensitive regexes)
  run over the corpus. All four gates are evidenced in this campaign;
  `skipped: []`.
- Generalization by construction: the prior bodies are fixed constants
  distilled from the ratified records (falsify enforcement from the P3/P16
  arc and the detector season that falsified its own premise; the
  band-mask guard from the F5 calibration finding and the lint
  `band_mask_warning`; stall-resume from the progress-vs-runtime stall bug
  and the salvage-to-landing arc; DRIFT retirement from the corpus-matrix
  re-seal arc). The scan only SELECTS gates; it never writes content, so
  no sid, campaign name, or absolute path can leak. Emitted priors were
  grepped for `s[0-9]`: zero matches.
- Draft location: `<root>/.rumpun/plugins/<name>-draft/` (beside installed
  packs; `plugin install` is the promotion path and re-gates everything:
  digest verify, lint gate, priors-only copy).
- Self-gate: `plugin_distill` runs `plugin_lint` on its own staged output
  and refuses to emit a draft with any error finding.
- Atomicity: staging dir under `plugins/`, digest sealed over staged
  priors/, `os.replace` at the end; any failure path removes the staging
  dir. Re-running replaces the previous draft. Source records are never
  mutated.

## Spec deviation, flagged

- The deliverable text says `private_vocabulary: []`. The strict v1 schema
  (`REQUIRED_KEYS`, `_manifest_findings`) rejects an empty list, and the
  acceptance gate is lint passing on the emitted pack. The two cannot both
  hold, so the draft emits `private_vocabulary: ["sid"]` — the
  season-identifier token class, campaign-agnostic and private in every
  campaign while being no campaign's name. Everything else in the manifest
  is exactly as specified: name, version 0.1.0, digest over priors/,
  source note verbatim.

## Repro (verified real, exit 0)

```
cd /mnt/data/work/rumpun
PYTHONPATH=<ws>/scratch/src .venv/bin/python -m rumpun plugin distill \
  kaggle-base --source "distilled from a 50-season campaign"
```

- exit 0; all four gates distilled (`skipped: []`); draft at
  `.rumpun/plugins/kaggle-base-draft`; digest
  `3b5399f0b37d6cf42f9ddcdb617373923eedbe074a35dd52dbbeaff78a7a2801`.
- Emitted tree: `manifest.yaml` + 4 priors files
  (falsify-enforcement, band-mask-guard, stall-resume, drift-retirement).
- Manifest readback: digest sealed, `private_vocabulary: ["sid"]`, source
  verbatim.
- Independent verification (`scratch/verify_distill.py` on the emitted
  pack): module resolved from `scratch/src` (probe logged), computed
  `priors_digest` equals the manifest digest, `plugin_lint`: 0 findings,
  0 errors.
- Repro artifact removed after evidence was captured; `git status` shows
  only pre-existing deltas (four `logs/*` files, `replay-matrix.md`,
  untracked `.rumpun/seasons/s51.yaml` — none from this session).

## Ruff

- `ruff check --no-respect-gitignore` on plugin.py, cli.py,
  verify_distill.py: all clean. One real catch during iteration (missing
  colon in `_distill_corpus`) was fixed before anything ran.

## Suite

Running against the repo suite with `PYTHONPATH=<ws>/scratch/src`
(result appended when the run lands).
