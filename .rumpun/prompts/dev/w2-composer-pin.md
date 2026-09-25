# s111 w2 — the composer's fourth render lands as a pinned deliverable

The composer clause has ridden briefs since s103 without landing as a
deliverable. This lane lands it: render the pack over the live campaign
and prove the digest equality as a pin in the repo suite.

## Ground truth (measured 2026-09-20)
- the seam: src/rumpun/plugin.py, priors_digest(pack_dir) at line 368;
  the digest registry the checker reads is .rumpun/plugins.yml
- the close check's DIGESTS pass recomputes every claimed pack digest
  in the archive extract (tools/artifact_check.py, the pack digest
  kancil-base line in the check-s108-2 record)
- the digest is LIVE: any priors/ edit moves it; s110 changed no priors
  and the check matched claimed == recomputed
- the reseal race: probe the manifest state before any digest write;
  sibling sessions reseal too (the s103/s104 precedent)

## Task
1. Land the composer pin: tests/test_s111_composer_pin.py renders the
   composer pack (or computes priors_digest) over a fixture pack dir
   and asserts the digest equality the close check enforces (claimed ==
   recomputed; a mutated prior moves the digest). Red-first.
2. Render the fourth pass for real over the live campaign: recompute
   the kancil-base digest, compare against the registry claim, record
   both in notes.md. Do NOT rewrite the manifest if they match; if they
   drift, report the drift in notes.md and stop (the close worker owns
   reseals).
3. notes.md REQUIRED before ending the turn: the pin result, both
   digest values, the suite count. Never wait on a background job at
   turn end (the s108 w1 lesson).

## Bounds
- Edits: src/rumpun/plugin.py (only if the pin needs a seam),
  tests/test_s111_composer_pin.py only. notes.md REQUIRED.
