# s51 w2 — spec-first pins for the extended distill

You are w2 in season s51 (repo root: the parent of this .rumpun tree).
Read src/rumpun/plugin.py (plugin_distill, DISTILLED_PRIORS, plugin_lint),
akar records s50-harvest + audit-38, and the s50 pins (tests/
test_s50_w2_pins.py) as the shape precedent. You own tests/; w1 owns
plugin.py. FILE TOOLS directly. WRITE ONLY inside your workspace. 40
minutes.

## Spec-first pins (red against current code)

1. The extended emission: `plugin distill kaggle-base --source <note>`
   (subprocess, 120s bound) emits priors/ gates PLUS evidenced patterns in
   priors/patterns/ and templates in priors/templates/, selected from the
   ratified records.
2. The new content carries no campaign privates: no sid token, no
   absolute-path token, no campaign name token in any patterns/ or
   templates/ filename or content line (the s50 pin-2 shape, applied to
   the new classes).
3. The manifest digest verifies over the full priors/ tree (gates +
   patterns + templates), and `plugin install` on the draft installs the
   pack round-trip.
4. Regression: the suite holds its floor — additions-only vs tests/, and
   the four known reds (3 s43 coverage pins, 1 race flake) stay the only
   reds.

## Constraints
- tests/ additions-only vs the current repo file; existing tests stay untouched.
- The pins run the distill via subprocess, timeout bounded (120s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns plugin.py; the harness merges.

## Verify before finishing
Measured red set against current code in notes.md; the four known reds
stay the only reds in the full suite.
