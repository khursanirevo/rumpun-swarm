# s47 w1 — the plugin machinery's completion

You are w1 in season s47 (repo root: the parent of this .rumpun tree). Read
src/rumpun/plugin.py (your s46 module), src/rumpun/cli.py (the s46 wiring),
tests/test_s46_w2_plugin_pins.py (the pins whose interface you reconcile),
and akar records audit-35 + s46-harvest. FILE TOOLS directly. WRITE ONLY
inside your workspace. 40 minutes.

## Deliverables (workspace copies of plugin.py + cli.py)

1. resolve_prompt(root, rel): the pins' named interface — first installed
   pack whose priors tree carries rel wins; fallback root/rel. (Your
   resolve_template logic, renamed to the pinned name; keep
   resolve_template as an alias if init_project calls it.)
2. The manifest gates accepting the pinned fixture packs' schema shape
   (the pins' _s46w2_pack fixtures: the manifest fields as w2 declared
   them) — reconcile the schema, not the pins.
3. The installer excluding campaign/: the staged copy carries priors/ only
   (the boundary pin's contract: campaign/ content never lands).

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- The suite stays green (the pins' failures are your spec).

## Verify before finishing

w2's pins file (tests/test_s46_w2_plugin_pins.py) run against your
patched copies: 7/7 green. Suite green. Both in notes.md.
