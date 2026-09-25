# s89 w1 — sync the installed pack; extend the board-arc epic

The campaign runs kancil-base 0.1.0 at digest cb5203; the re-sealed
draft is ab03f431 (the correctness prior landed at s88). Sync the
installed copy, then extend the epic.

## Ground truth (measured 2026-09-17)
- installed: kancil-base 0.1.0 @ cb5203 (plugin list); draft re-sealed
  @ ab03f431 with verdict-vs-correctness.md new in priors/templates/
- .rumpun/epics.yaml: board-arc carries s69-s84; s85-s88 sit in the
  campaign epic (they closed after the split)

## Task
1. Reinstall: `rumpun plugin install .rumpun/plugins/kancil-base-draft`
   — the installed copy updates to ab03f431 digest-verified.
   `rumpun plugin list` shows the new digest.
2. Extend the board-arc epic: epics.yaml gains s85-s88 (the arc's
   seasons; the campaign epic keeps the rest). Preserve every verdict
   (the s85 split arithmetic rule: the two views must sum to the
   whole).
3. Verify: the epic view renders both epics, the arithmetic sums, and
   the s77 version pins stay green (the pack content changed — the
   version stamp did not).
4. notes.md REQUIRED: the old/new digests, the epic view output, the
   arithmetic check.

## Bounds
- Edits: .rumpun/epics.yaml only. No priors content edits. notes.md
  REQUIRED.
