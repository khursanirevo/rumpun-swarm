# akar record: check-s54
id: check-s54
date: 2026-09-16
title: independent artifact check s54 @ 614aabf5a4a0 (VERIFIED)
season: s54
close-commit: 614aabf5a4a017e84b08caa60c57f7098afdc627
outcome row: WIN (all band clauses met)
extracted: git archive -> temp tree (716 files)
commands run:
- git -C /mnt/data/work/rumpun rev-parse --verify 614aabf^{commit} -> 614aabf5a4a017e84b08caa60c57f7098afdc627
- git -C /mnt/data/work/rumpun archive 614aabf5a4a0 -> 716 files
- /mnt/data/work/rumpun/.venv/bin/python -m pytest ['test_s54_w2_rename_pins.py'] -q (exit 0)
pins: exit 0; collected 8, passed 8, failed 0, errors 0; 4.0s; probe resolved /mnt/data/tmp/artifact-check-boya3w6p/tree/src/rumpun/__init__.py
packs: no .rumpun/plugins.yml in the extracted tree (no pack digest claims)
seal 2026-09-16_s54-harvest.md: claimed 7340c8c39eb10402.. recomputed 7340c8c39eb10402.. -> MATCH
ships row (verbatim): writers: is the schema key drafts emit (benih: reads back-compat in lint/engine/evolve), the CLI surface is English (harvest help, evolve reject/rollback paths, audit help, the akar.py stderr line), the direct verb reads and writes .rumpun/ledger/directives.jsonl with the stray akar/ record migrated, season list reads the real seasons dir (the musim/ glob was a dead path - a latent s45 defect found and fixed), 8 pins, and the four draft-format pins re-sealed per the s48 precedent; suite 243/243
ships diff:
| named ship | verdict | evidence |
|---|---|---|
| writers: is the schema key drafts emit (benih: reads back-compat in lint/engi... | MATCH | writers: PRESENT (src/rumpun/evolve.py:125); benih: PRESENT (src/rumpun/engine.py:727); lint/engine/evolve PRESENT (module reading: src/rumpun/lint.py, src/rumpun/engine.py, src/rumpun/evolve.py); writers: PRESENT (src/rumpun/lint.py:426); benih: PRESENT (src/rumpun/engine.py:727) |
| the CLI surface is English (harvest help, evolve reject/rollback paths, audit... | MATCH | file src/rumpun/akar.py exists; rollback PRESENT (src/rumpun/cli.py:5) |
| the direct verb reads and writes .rumpun/ledger/directives.jsonl with the str... | MATCH | file .rumpun/ledger/directives.jsonl exists; akar/ PRESENT (module reading: src/rumpun/akar.py) |
| season list reads the real seasons dir (the musim/ glob was a dead path - a l... | MATCH | musim PRESENT (src/rumpun/audit.py:3); musim/: legacy token still in src (evidence; the removal claim itself is judged by the pins) |
| 8 pins | MATCH | pins claim 8 == collected 8 |
| and the four draft-format pins re-sealed per the s48 precedent | MATCH | no machine-checkable claims (prose clause) |
| suite 243/243 | MATCH | 243/243: metric token, not a surface; suite claim 243/243 recorded, not re-run |
suite claim: 243/243 recorded, not re-run
verdict: VERIFIED
sha256: ab0012c6f839f7d559d7be8c179a0e1069c5798a019b4ea31930906c766d5692
