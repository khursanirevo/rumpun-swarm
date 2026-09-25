# s50 w1 — plugin distill: the flywheel's export

You are w1 in season s50 (repo root: the parent of this .rumpun tree). Read
src/rumpun/plugin.py (the s44 pack format + the s46 install machinery),
DESIGN.md sections 13-16 (the proven gates), and akar records audit-38 +
s44-harvest + s46-harvest. FILE TOOLS directly. WRITE ONLY inside your
workspace EXCEPT minimal documented cli.py wiring. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. plugin.py gains plugin_distill(root, pack_name, source_note): scans the
   campaign's proven gates and patterns (the falsify enforcement, the
   band-mask guard, the stall-resume pattern, the DRIFT retirement —
   distilled from the DESIGN's ratified records into generalized priors),
   drafts the pack schema (the manifest: name, version 0.1.0, digest
   computed over priors/, private_vocabulary: [], source: the note), and
   writes the pack to root/plugins/<name>-draft/ for review.
2. cli.py wiring (minimal, documented): `rumpun plugin distill
   <pack_name> --source <note>`.

## Constraints

- The distilled priors are GENERALIZED (no project sids, no campaign
  names — the guardrails lint's rules apply to the distill's own output).
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- The suite stays green (the distill is additive).

## Verify before finishing

Repro: plugin distill kaggle-base --source "distilled from a 50-season
campaign" emits the pack draft with priors/ content, the manifest digest
computed, and plugin lint passing on the emitted pack. Suite green.
All in notes.md.
