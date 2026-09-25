# s258 w2 — the one diff

The proposer lane: turn the scorer's top finding into one
evidence-cited fix proposal for the operator to merge.

## Ground truth (measured 2026-09-24)
- the scorer's report: the w1 lane's process-score record (read it
  fresh at run time; enumerate, never copy)
- the proposal target: the single highest-frequency failure class
  in the report. Expected candidates (corroborated drifts):
  the frozen-brief fill step (record targets froze at s214 names,
  forty-plus lanes adapted by hand) and the harvest-only close
  (s214-s254 skipped DESIGN entries, commits, pushes)
- the merge gate: proposals stay reviewable diffs; the OPERATOR
  merges; the lane never applies its own proposal to rules files,
  templates, or CLAUDE.md
- routing (operator directive 2026-09-24): every proposal names one
  bin, useful-only, no accretion:
  1. campaign-local -> rumpun's own templates/briefs/seed step,
     landed through a normal close
  2. user-global -> an on-demand reference file
     (~/.claude/references/<topic>.md), loaded only when relevant
  3. generalizes across projects -> a skills plugin repo in the
     builderio/skills shape (SKILL.md per skill, .claude-plugin
     marketplace metadata, install on demand); ambient rules blocks
     stay out unless the rule is truly always-on
  default order 1 > 2 > 3; promotion to the next bin needs evidence
  of general use
- evidence discipline: the proposal cites the failing seasons

## Task
1. Read the scorer's report; pick the top failure class by count.
2. Draft ONE fix as a unified diff plus rationale, saved to
   .rumpun/proposals/process-diff-<date>.md (create the dir).
3. Verify: the diff passes git apply --check against a scratch
   checkout; land the record under tests/ with the next free
   per-family process-diff name; solo pins green; ruff clean.
4. notes.md REQUIRED before ending the turn (top class, counts,
   the diff's target file, apply-check rc). Never wait on a
   background job at turn end.

## Bounds
- Repo edits: the proposal file and the one new record file only.
  Rules files, templates, CLAUDE.md, RESUME stay untouched.
