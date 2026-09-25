# s44 w1 — the pack format + the plugin guardrails lint

You are w1 in season s44 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-16, src/rumpun/lint.py (the house lint pattern), and
the operator's plugin/hub directive (the direct ledger, 2 pending). FILE
TOOLS directly. WRITE ONLY inside your workspace EXCEPT minimal documented
cli.py wiring for the new verb. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. src/rumpun/plugin.py (new module, workspace copy):
   - the pack manifest schema: name, version, base (lineage, optional for
     bases), digest, private_vocabulary (list), source (provenance note)
   - pack content classes: priors/ installs and publishes; campaign/ never
     does - structurally, the installer's discovery reads priors/ only
   - plugin_lint(pack_dir, manifest): rejects sids (s\d+ tokens), absolute
     paths, private-vocabulary matches, and manifest violations - each
     offense named with file and line, exit nonzero
2. cli.py wiring (minimal, documented): `rumpun plugin lint <packdir>`
3. notes.md: schema decisions + verification

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch audit.py, collab.py, engine.py, harvest.py, evolve.py,
  lint.py, report.py, tests/ (w2 owns the pins; the harness merges).
- The 188-test suite stays green.

## Verify before finishing

Repros: a valid minimal pack passes; a pack with a sid in priors/ fails
naming file and line; a private-vocabulary match fails; a campaign/ dir
is invisible to the installer's discovery. Suite green against patched
copies. All in notes.md.
