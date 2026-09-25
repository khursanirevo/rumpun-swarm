# s53 w2 — spec-first pins for the hub round trip

You are w2 in season s53 (repo root: the parent of this .rumpun tree).
Read src/rumpun/plugin.py (hub v1 design, plugin_install, plugin_lint,
priors_digest) and akar records s52-harvest + audit-38; the s50/s51 pins
are the shape precedent. You own tests/; w1 owns plugin.py + cli. FILE
TOOLS directly. WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. The round trip over a LOCAL bare git remote (file path; no network):
   `plugin publish` exits 0 with a lint-gate pass and digest verify;
   `plugin pull <name> --remote <path>` installs the pack into a fresh
   campaign root; the pulled pack's digest equals the published pack's
   digest and plugin_list records it.
2. The guardrails hold on the wire: a pack failing the lint gate refuses
   to publish; campaign/ content never appears at the remote; a tampered
   remote digest fails the pull.
3. Regression: the suite floor holds (additions-only; the s43 pins stay
   green; race flakes aside).

## Constraints
- tests/ additions-only; the pins subprocess the verbs, timeout bounded.
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ - w1 owns plugin.py + cli; the harness merges.

## Verify before finishing
Measured red set in notes.md; the round trip + guardrail pins green at
merge; the four known reds otherwise unchanged.
