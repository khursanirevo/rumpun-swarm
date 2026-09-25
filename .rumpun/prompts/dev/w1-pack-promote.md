# s81 w1 — promote kancil-base from draft to installable release

The draft has been a draft since s67; it is now materially complete
(the operating skills from the 2.2.5 source read, the repro-backed
closure contract from s80). Promotion is the deliverable.

## Ground truth (measured 2026-09-17)
- .rumpun/plugins/kancil-base-draft/: manifest v0.1.0 digest-sealed,
  priors/ (patterns, templates, skills/kancil-2.2-skills.md stamped
  2.2.5@7700a1b), the repro-backed-closure template (s80)
- plugin.py: plugin_install promotes a draft (digest-verified) into a
  campaign; the digest convention: sha256 over sorted priors/
- a fresh `rumpun init --plugin <dir>` installs pack-first

## Task
1. Review the draft as a release: every prior reads clean, the
   manifest's digest matches a fresh recompute, the version is right
   (0.1.0 is honest for a first promoted release).
2. Promote in the LIVE campaign: `rumpun plugin install
   .rumpun/plugins/kancil-base-draft` (or the promoted path per
   plugin.py's convention) — the campaign itself runs the pack.
3. Prove the fresh-campaign path: scaffold a throwaway campaign with
   `rumpun init --plugin <draft>` in /tmp, verify the pack installs
   digest-verified and the skills file ships with it. Delete the
   throwaway after.
4. Verify: `rumpun plugin list` shows kancil-base in the live
   campaign; the s69 board pins + the s77 version pins stay green.
5. notes.md REQUIRED: the digest, the install receipt, the
   throwaway's verification output.

## Bounds
- The draft dir is the source of truth; do not edit priors content.
  No live kancil call. notes.md REQUIRED.
