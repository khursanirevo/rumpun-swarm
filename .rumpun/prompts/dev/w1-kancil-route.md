# s67 w1 — the kancil route and the kaggle scaffold

You are w1 in season s67 (repo root: /mnt/data/work/rumpun; the kancil
repo lives at /mnt/data/work/kancil). Read src/rumpun/cli.py, rumpun.yaml
(the routes map), ../kancil's README/CLI entry (how kancil is invoked),
and ledger records s66-harvest + audit-42 + directives seq 2 (kaggle-base
is the first pack) and seq 9/10. FILE TOOLS directly. WRITE ONLY inside
your workspace EXCEPT minimal documented rumpun.yaml + scaffold changes.
40 minutes.

## Deliverables (workspace copies; the harness merges)

1. The kancil route: a `kancil:` entry in rumpun.yaml's routes map whose
   command pipes the rendered prompt into kancil's real CLI entry
   (inspect ../kancil for the exact invocation; document it in the route
   comment).
2. The kaggle-base pack: regenerate the distill
   (`rumpun plugin distill kaggle-base --source "the campaign's proven
   gates and patterns"`) and prove `plugin install` lands it in a fresh
   scaffolded campaign (digest verified).
3. The competition season template: a lint-clean template yaml at
   prompts/base or seasons/ with the phases baseline -> validate ->
   submit -> improve, the competition metric as the band, and
   "submission scores" as the falsify gate; document the fill-in fields.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- Additive: the suite floor holds; the known race flakes stay the only reds.

## Verify before finishing
A fixture campaign with the kancil route runs a stub season to
completed; kaggle-base installs digest-verified; the template lints.
Suite floor. All in notes.md.

## Correction (2026-09-16, operator: install kancil from pip)
- kancil installs as a pip package, NOT the local source tree: the
  campaign venv runs `uv pip install /mnt/data/work/kancil` (package
  name kancil, version 2.2.4; not on public PyPI - a git URL installs
  the same way for sharing). The route invokes the INSTALLED `kancil`
  CLI from PATH, never a source-tree path.
- Inspect the installed package (`kancil --help`) for the invocation;
  the campaign setup step performs the install.

## Correction (2026-09-16, directive seq 12): the pack is kancil-base
- The first pack name is KANCIL-BASE, not kaggle-base: the pack serves
  kancil-driven campaigns of any domain. Kaggle specifics fold in as
  content sections; a venue-specific pack can later declare
  base: kancil-base lineage. The distill command:
  `rumpun plugin distill kancil-base --source "..."`.
