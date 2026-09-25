# s51 w1 — the distill extends: patterns + templates inside priors/

You are w1 in season s51 (repo root: the parent of this .rumpun tree).
Read src/rumpun/plugin.py (the s50 plugin_distill + DISTILLED_PRIORS),
DESIGN.md sections 13-16 (the proven gates AND the working patterns), and
akar records s50-harvest + audit-38. FILE TOOLS directly. WRITE ONLY inside
your workspace EXCEPT minimal documented plugin.py changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. plugin.py extends plugin_distill: the scan selects evidenced PATTERNS
   and TEMPLATES from the same ratified records, not only the four gates.
   They land inside priors/ (priors/patterns/<key>.md,
   priors/templates/<key>.md) — the s44 v1 schema stays unchanged; the
   digest already covers the full priors/ tree.
2. Candidate axes (the scan decides by evidence in the ratified records):
   patterns — spec-first pinning (w2 pins red, then green at merge), merge
   reconciliation, harvest close, the replay corpus gate; templates —
   season yaml, harvest note, pins file header, the akar record shape.
3. Content is generalized: no sids, campaign names, absolute paths, or
   campaign-private terms; plugin_lint's rules apply to the distill's own
   output (self-lint, refuse on error). cli wiring unchanged.

## Constraints
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- The suite holds its floor: additive change, the four known reds stay the only reds.

## Verify before finishing
Repro: `plugin distill kaggle-base --source "extended from the campaign"`
emits priors/ gates PLUS priors/patterns/ and priors/templates/, the
manifest digest verifies over the full priors/ tree, plugin lint clean,
and the install round-trip lands the pack. All in notes.md.
