# s50 w2 — spec-first pins for plugin distill

You are w2 in season s50 (repo root: the parent of this .rumpun tree). Read
src/rumpun/plugin.py, akar records audit-38 + s44-harvest. You own tests/;
w1 owns plugin.py + cli. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Spec-first pins (red against current code)

1. Distill emits the pack: priors/ content extracted from the proven
   gates, the manifest with the computed digest, plugin lint passing on
   the emitted pack.
2. The distilled priors contain no project sids or campaign names (the
   guardrails lint's own rules applied to the distill's output).
3. install --plugin on the emitted pack installs it (the round trip:
   distill -> install -> the campaign's plugins dir holds the pack).
4. Regression: the suite stays green.

## Constraints

- tests additions-only vs the current repo file (188 tests kept).
- The pins run the distill via subprocess, timeout bounded (120s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns plugin.py + cli.

## Verify before finishing

Measured red set against current code in notes.md; the 188 existing
tests green.
