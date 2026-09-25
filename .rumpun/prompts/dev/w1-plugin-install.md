# s46 w1 — plugin install/list/use in plugin.py + cli

You are w1 in season s46 (repo root: the parent of this .rumpun tree). Read
src/rumpun/plugin.py (the s44 pack format + plugin_lint), src/rumpun/cli.py
(the verb wiring pattern), and akar records audit-34 + s44-harvest. FILE
TOOLS directly. WRITE ONLY inside your workspace EXCEPT minimal documented
cli.py wiring. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. plugin.py gains:
   - plugin_install(root, pack_dir): verifies the pack digest, runs
     plugin_lint, copies priors/ into root/plugins/<name>/ (digest-verified,
     atomic), records the install in the campaign's plugins.yml
   - plugin_list(root): installed packs with name, version, digest
   - scaffold support: init --plugin <name> resolves templates/prompts from
     the installed pack before the base tree
2. cli.py wiring (minimal, documented): `rumpun plugin install <packdir>`,
   `rumpun plugin list`

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch audit.py, collab.py, engine.py, harvest.py, evolve.py,
  lint.py, report.py, tests/ (w2 owns the pins; the harness merges).
- The 188-test suite stays green.

## Verify before finishing

Repros: install a valid pack -> plugins/<name>/ holds priors/ and the
install record; install a tampered pack (digest mismatch) -> refused
naming the pack; list shows the installed pack. Suite green against
patched copies. All in notes.md.
