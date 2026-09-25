# s96 w1 — the pack resync; the epic extends (the s89 pattern, second pass)

Maintenance with live verification: the installed pack trails the
re-sealed draft by the s92-s94 priors; the board-arc epic trails by
s94-s95.

## Ground truth (measured 2026-09-18)
- installed: kancil-base 0.1.0 @ ab03f431 (the s89 sync); the draft
  re-sealed since at 16420f93, then 09db9869 (the s93 templates), then
  16420f93 again (the s94 stopping rule + cost accounting) — verify
  the CURRENT draft digest fresh, never trust the notes
- .rumpun/epics.yaml: board-arc carries s69-s88; s89-s95 sit in the
  campaign epic (s89-s92 closed after the s89 split, s93-s95 after)

## Task
1. Verify the draft digest fresh (probe, don't trust): recompute over
   priors/, compare to the manifest.
2. Reinstall: `rumpun plugin install .rumpun/plugins/kancil-base-draft`
   — the installed copy updates to the current digest. `rumpun plugin
   list` shows it; the correctness prior AND the four new priors
   (baseline-comparison, completion-effort, stopping-rule,
   cost-accounting) present in the installed copy.
3. Extend the board-arc epic: epics.yaml gains s94-s95 (s89-s92
   landed in the s89 pattern... verify which seasons the campaign
   epic still holds and extend accordingly). Preserve every verdict
   (the pinned arithmetic rule).
4. Verify: the epic view renders both epics summing to the whole
   ledger; lint passes; the s77 version pins + the s89 arithmetic
   pins stay green.
5. notes.md REQUIRED: the digests, the epic view output, the
   arithmetic check.

## Bounds
- Edits: .rumpun/epics.yaml only. No priors content edits. notes.md
  REQUIRED.
