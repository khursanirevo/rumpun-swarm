# s70 w2 — panel tooling, first slice (the seeded issue #1)

Directive seq 0: "seasons stay manual until panel tooling lands". This
season lands the panel's input contract and a dry-run surface; the real
second-opinion route lands next season.

## Ground truth
- lint.py already emits findings; the season-start warning says "lint
  passes; panel will not" - the panel is the stronger reviewer that
  does not exist yet
- tools/usefulness_audit.py composes audits; s69-harvest records the
  s69 outcome; schema: 1 campaigns carry .rumpun/CHANGELOG.md

## Task (spec-first, pins in tests/test_s70_w2_pins.py, _s70w2_ prefix)
1. src/rumpun/panel.py: `claim_set(root, sid)` - the deterministic
   input the panel would review for a season: the season yaml's
   goal/expected_band, the harvest record's implies/observed lines, the
   suite count from the DESIGN ships row. Pure file reading; no network.
2. `render_review(claims)` - the exact text a second-opinion route
   would receive (bounded, one screen).
3. CLI: `rumpun audit --panel <sid> --dry-run` prints the rendered
   review; without --dry-run it appends a `panel-<sid>` ledger record
   marked pending (the sha-sealed akar discipline; the verdict comes
   from the route next season).
4. Pins: claim_set reads the real s69 files in a fixture campaign;
   render_review is stable and bounded; the pending record seals.

## Bounds
- 40-60 min budget. No edits outside src/rumpun/panel.py, cli.py wiring,
  and tests/. notes.md REQUIRED. No route calls this season.
