# s131 w2 — the pack teaches the competition season

The scaffold emits the competition-season shape; the kancil-base
priors do not teach what a competition season owes. Refresh.

## Ground truth (measured 2026-09-20)
- the priors: .rumpun/plugins/kancil-base/priors/ (second-opinions.md
  and exit-artifacts.md landed at s120; the pack lint bans season ids -
  templates stay campaign-agnostic)
- the digest: src/rumpun/plugin.py priors_digest; the registry claim
  lives in .rumpun/plugins.yml; the equality is enforced by the close
  check and pinned by tests/test_s111_composer_pin.py
- the traps: the digest is LIVE (any priors edit moves it); sibling
  sessions reseal too - probe the manifest before any digest write,
  and the reseal lands in the same close so the check's digest pass
  matches (the s120 precedent)
- the lesson to teach: a competition season owes an external outcome,
  a named baseline, and the honest unmeasured note when neither exists

## Task
1. Add priors/competition-season.md, campaign-agnostic: what a
   competition season owes (the external outcome, the named baseline,
   the honest unmeasured note), the guide's template pointer. Probe
   the manifest, recompute the digest, reseal the registry in this
   close - the digest moves here or nowhere. Pins in
   tests/test_s131_priors_competition.py (the template lint and the
   digest equality).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: .rumpun/plugins/kancil-base/priors/competition-season.md,
  .rumpun/plugins.yml (the reseal only),
  tests/test_s131_priors_competition.py only. notes.md REQUIRED.
