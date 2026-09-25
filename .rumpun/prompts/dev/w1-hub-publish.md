# s53 w1 — hub v1: publish and pull over git

You are w1 in season s53 (repo root: the parent of this .rumpun tree).
Read src/rumpun/plugin.py (the module docstring's hub v1 design,
plugin_lint, priors_digest, plugin_install), DESIGN.md sections 13-16,
and akar records s52-harvest + audit-38. FILE TOOLS directly. WRITE ONLY
inside your workspace EXCEPT minimal documented plugin.py + cli.py
changes. 40 minutes.

## Deliverables (workspace copies; the harness merges)

1. plugin.py gains plugin_publish(root, pack, remote): lint-gates the
   pack (zero errors), verifies the digest over the installed tree, then
   pushes it as a git repo to REMOTE (pack = repo, publish = push).
2. plugin.py gains plugin_pull(root, name, remote): fetch from REMOTE,
   digest-verify the received priors/ tree, then the standard install
   path (s46 machinery: lint gate, priors-only copy, plugins.yml
   record). campaign/ is structurally invisible to both verbs.
3. cli.py wiring (minimal, documented): `rumpun plugin publish <name>
   --remote <url>` and `rumpun plugin pull <name> --remote <url>`.

## Constraints
- Git ops via subprocess git; tests use file-path remotes (no network).
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch tests/ (w2 owns the pins; the harness merges).
- Additive: the suite floor holds, the known race flakes stay the only reds.

## Verify before finishing
Publish kaggle-base to a local bare repo, pull into a fresh `rumpun
init` campaign: digest equal, plugin list shows it. Suite floor. All in
notes.md.
