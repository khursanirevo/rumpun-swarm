# s46 w1 notes

## What landed
plugin install/list/use in workspace copies of plugin.py + cli.py.

src/rumpun/plugin.py (appended under the s46 section marker):
- priors_digest(priors_dir): sha256 over (rel path, NUL, bytes, NUL)
  triplets in sorted rel-path order. This DEFINES the tree digest — no
  prior convention existed (s44 pins used placeholder digests).
- plugins_dir(root), plugins_registry_path(root) -> .rumpun/plugins.yml.
- plugin_install(root, pack_dir): gates manifest load -> schema-valid name
  -> digest match -> plugin_lint; every refusal names the pack. priors/
  copies through a staging dir re-digested before the atomic rename;
  re-install replaces the old tree only after the new copy verifies.
  campaign/ is structurally invisible (discover_priors walk). The install
  record lands in .rumpun/plugins.yml under flock + atomic replace.
- plugin_list(root): registry rows sorted by name (name, version, digest,
  installed_at, source).
- resolve_template + init_project(target, plugins): init --plugin resolves
  every .rumpun-relative scaffold output from priors/<rel> of the first
  pack carrying it; base tree fallback; uninstalled names fail before any
  write. No plugins -> scaffold.init_project verbatim.

src/rumpun/cli.py (anchored, documented edits):
- new plugin group: `rumpun plugin install <packdir>` (campaign root =
  cwd; no .rumpun required, so install can precede init — the init
  --plugin flow needs that), `rumpun plugin list` (name/version/digest
  lines).
- `rumpun init --plugin NAME` (repeatable, first match wins): cmd_init
  routes through plugin.init_project, which delegates to
  scaffold.init_project when the list is empty.
- main() maps PluginError to exit 1.
- `plugin lint` stays unwired (s44 w1's cli patch never merged; outside
  s46 scope) — follow-up.

## Measured (this workspace)
- verify: 12/12 repros PASS (results.jsonl): install valid pack (tree +
  record), campaign/ never copied, tampered pack refused naming the pack,
  tamper copies nothing, plugin_list fields, pack-first scaffold + base
  fallback, season lints clean after the FILL step, uninstalled name fails
  writing nothing, re-install replaces tree + record.
- CLI smoke: plugin install / plugin list / init --plugin exit 0
  (repro-empty probe).
- ruff: clean on both files (--no-respect-gitignore).
