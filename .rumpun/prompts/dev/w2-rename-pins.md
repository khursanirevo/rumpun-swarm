# s54 w2 — spec-first pins for the finished rename

You are w2 in season s54 (repo root: the parent of this .rumpun tree).
Read src/rumpun/lint.py, src/rumpun/engine.py, src/rumpun/cli.py, the
newest operator directive (ledger directives), and akar records
s53-harvest + audit-38; the s45 rename pins (tests/test_s45_w2_rename_pins.py)
are the precedent. You own tests/; w1 owns src/. FILE TOOLS directly.
WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. A season yaml with `writers:` lints clean and starts; a yaml with
   `benih:` still lints clean (back-compat) and starts identically -
   same roster, same budgets.
2. The user-facing strings are English: the harvest help text, the
   evolve reject and rollback messages name the real paths; no "benih",
   "tuai", "musim", or "akar" survives in `--help` output or stderr
   messages (grep the parser help).
3. Back-compat is pinned, not implied: the old key still reads, the new
   key is what draft_next writes.

## Constraints
- tests/ additions-only; the s45 rename pins file stays byte-identical.
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ - w1 owns src/; the harness merges.

## Verify before finishing
Measured red set in notes.md; the rename pins green at merge; the two
known race flakes stay the only reds.

## Scope correction (2026-09-16, operator: focus on the rename)
- Add one pin: no "rimba" survives in user-facing strings (the audit F1
  phase-liveness text, the `season report --serve` help). The rimba/
  directory is already gone from the tree.
- Add one pin: a season yaml citing `ledger:<id>@<sha>` lints clean, and
  `akar:<id>@<sha>` still resolves (the alias holds). New citations
  prefer ledger:.
- GLOSSARY.md already maps all five pairs; it stays byte-identical
  unless the schema keys move (then the benih row notes the retirement).
