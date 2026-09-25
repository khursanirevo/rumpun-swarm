# s126 w2 — the kancil plugin cannot silently drift

The operator's seq 13: kancil improves itself through issue, PR, and
merge. The kancil-base plugin trails the installed CLI; nothing names
the gap.

## Ground truth (measured 2026-09-20)
- the plugin: .rumpun/plugins/kancil-base/ (its manifest declares a
  version)
- the CLI: the installed kancil (uv tool install kancil; the version
  subcommand answers)
- the honest shape: the plugin may legitimately trail the CLI - the
  drift reading is a named warning, not a hard failure; equality
  passes quietly
- fixture discipline: read versions only; no installs, no network in
  pins

## Task
1. Land the parity pin: it reads the kancil-base plugin's declared
   version and the installed kancil CLI version, passes on equality,
   and on drift names both versions in the failure message (the
   operator decides the upgrade). Pins red-first in
   tests/test_s126_kancil_parity.py.
2. Verify: solo pins green (or the drift honestly named); full suite
   green vs the known reds (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: tests/test_s126_kancil_parity.py, src/rumpun/plugin.py ONLY
  if a version-reading seam is needed. notes.md REQUIRED.
