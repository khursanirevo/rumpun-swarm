# s77 w1 — the kancil skills prompt, from a full source read (seq 15)

Kancil is rumpun's plugin route; a writer driving it needs the real
operating contract, not folklore. Build it from the source, stamped
with the version it describes.

## Ground truth (measured 2026-09-17)
- kancil source: /mnt/data/work/kancil, pyproject version 2.2.5;
  282 .py files, ~108k lines (read for contract, not line-by-line)
- installed: kancil v2.2.5 (uv tool list) - aligned today
- the s67 route: `kancil loop --prompt {prompt} --iteration-timeout
  1800`; the stop contract: KANCIL_STOP_FILE (merged s68, PR #138)
- the kancil-base pack draft: .rumpun/plugins/kancil-base-draft/
  (priors/, patterns/, templates/, manifest digest-sealed)

## Task
1. Systematic source sweep of /mnt/data/work/kancil: the CLI surface
   (every subcommand grouped by workflow: setup, experiments,
   evaluation, submission, monitoring), the loop/stop semantics
   (prompt file in, stop sentinel out, iteration-timeout), the kaggle
   verbs' contract, and the setup wizard's outputs. Read modules in
   dependency order; record per-module one-line summaries in notes.md
   as you go (the read must be reconstructable).
2. Distill into the kancil-base pack:
   priors/skills/kancil-2.2-skills.md - the writer-facing operating
   prompt: which verbs, in what order, what each returns, the stop
   behavior, the failure modes. Frontmatter: `kancil-version: 2.2.5`,
   `source-commit: <git -C /mnt/data/work/kancil rev-parse HEAD>`.
3. Re-seal the pack: bump the manifest digest (the digest covers
   priors/), keep version 0.1.0 unless content changed materially.
4. Verify: the skills prompt names ONLY verbs that exist in the
   source you read; spot-check five random claims against the code.

## Bounds
- Read-only on /mnt/data/work/kancil. Pack edits inside the draft
  dir. notes.md REQUIRED: the module map + the five spot-checks.
