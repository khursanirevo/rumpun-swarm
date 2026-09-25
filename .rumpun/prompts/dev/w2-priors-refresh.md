# s120 w2 — the priors teach the new conventions

The kancil-base pack is the distilled knowledge other campaigns start
from; it predates the rerun derivation, the notes gate, the dissent
marks, and the adjusted truth. Refresh it.

## Ground truth (measured 2026-09-20)
- the priors: .rumpun/plugins/kancil-base/priors/ (template markdown;
  the pack lint bans season ids - sid tokens never publish, keep every
  template campaign-agnostic)
- the digest: src/rumpun/plugin.py priors_digest (line 368); the
  registry claim lives in .rumpun/plugins.yml; the digest equality is
  enforced by the close check and pinned by tests/test_s111_composer_pin.py
- the traps: the digest is LIVE (any priors edit moves it); sibling
  sessions reseal too - probe the manifest state before any digest
  write (the s103/s104 precedent); the reseal and the templates land
  in the same close so the check's digest pass matches
- the conventions to teach, from the ledger: the second-opinion rerun
  derivation (a refusal becomes a naming convention), the notes gate
  (a missing artifact becomes a machine mark), the dissent marks (a
  disagreement renders, agreement stays quiet)

## Task
1. Add or refresh two priors templates, campaign-agnostic: one on
   second opinions (request, rerun derivation, dissent rendering),
   one on exit artifacts (what a writer owes, how the engine marks a
   gap). Probe the manifest, recompute the digest, reseal the
   registry in this close - the digest moves here or nowhere.
2. Verify: the close check's digest pass is the authority (it runs at
   this close); full suite green vs the known reds; ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: .rumpun/plugins/kancil-base/priors/*, .rumpun/plugins.yml
  (the reseal only), tests/test_s120_priors_refresh.py (optional
  template lint). notes.md REQUIRED.
