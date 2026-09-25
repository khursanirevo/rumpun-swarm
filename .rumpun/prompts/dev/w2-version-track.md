# s77 w2 — version tracking: the prompt matches the installed kancil (seq 15)

A skills prompt describes one kancil version; users run others. Your
slice: detect the mismatch and surface it as a NEED HUMAN card.

## Ground truth
- installed kancil v2.2.5 (uv tool list); source pyproject 2.2.5
- w1 lands priors/skills/kancil-2.2-skills.md with frontmatter
  `kancil-version: 2.2.5`
- kanban NEED HUMAN cards: the four-sentence shape, the s69/s75
  precedents; panel.py's latest_panel_record is the ledger-read
  precedent

## Task (spec-first, pins in tests/test_s77_w2_pins.py, _s77w2_ prefix)
1. src/rumpun/skills.py: `skills_version(pack_dir)` — the frontmatter
   kancil-version from the pack's skills file (pure read; None when
   absent). `installed_kancil_version()` — the installed package
   version via importlib.metadata.version("kancil") (offline; None
   when kancil is not installed). `version_aligned(pack_dir)` — True
   when equal, None when either side is unknown.
2. kanban.py grows _skills_cards(root): when a kancil-base pack is
   installed and version_aligned is falsy, one NEED HUMAN card (four
   sentences: which versions, what to run to re-align — `uv tool
   install --force /mnt/data/work/kancil` or the pack re-distill —
   why a human arbitrates, what happens if nobody acts). Aligned or
   unknown-both renders no card.
3. Pins: frontmatter parsing over fixture skill files; the alignment
   matrix (equal / prompt-newer / installed-newer / either-None); the
   card renders only on falsy alignment; the s69 degrade pin stays
   green.
4. cli wiring only if a verb is demanded; the card is the surface.

## Bounds
- Edits: src/rumpun/skills.py, src/rumpun/kanban.py, tests/. notes.md
  REQUIRED. No route call; no real pack mutation; no .rumpun edits.
