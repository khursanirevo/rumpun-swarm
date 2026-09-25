# s46 w2 — spec-first pins for plugin install/list/use

You are w2 in season s46 (repo root: the parent of this .rumpun tree). Read
src/rumpun/plugin.py, akar records audit-34 + s44-harvest. You own tests/;
w1 owns plugin.py + cli. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Spec-first pins (red against current code)

1. Install: a valid pack installs into the campaign's plugins dir with
   priors/ and the install record; a tampered pack (digest mismatch)
   is refused naming the pack.
2. List: plugin list shows the installed pack's name, version, digest.
3. Use: init --plugin scaffolds from the pack's templates (the
   scaffolded campaign's prompts resolve to the pack before the base).
4. Boundary holds post-install: campaign/ content from the pack is
   never copied into the campaign.
5. Regression: the 188-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (188 tests kept).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns plugin.py + cli.

## Verify before finishing

Measured red set against current code in notes.md; the 188 existing
tests green.
