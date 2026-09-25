# s82 w1 — the one-token reword, the re-seal, the promotion

The harness authorizes option 1 from your s81 predecessor's notes:
the content edit preserving meaning, then the re-seal, then the
promotion this draft has never passed.

## Ground truth (measured 2026-09-17)
- the blocker: priors/skills/kancil-2.2-skills.md:53 carries
  `/error-exp` in a backtick span; ABS_PATH_RE flags it (error
  severity); install refuses
- the digest three-way match held at d83e3b31... over 14 priors
- the lint-placement gap (distill skips the content lint) is issue
  #10 - NOT your lane; the re-seal here is the authorized exception

## Task
1. Edit priors/skills/kancil-2.2-skills.md:53: `/error-exp` ->
   `error-exp` (meaning preserved: it is a pointer label). One line.
2. Re-seal: recompute the digest over priors/, update the manifest's
   digest line (the s81 scratch/recompute_digest.py pattern).
3. Promote: `rumpun plugin install .rumpun/plugins/kancil-base-draft`
   - the gate that refused must now pass. `rumpun plugin list` shows
   kancil-base installed in the live campaign.
4. Re-run tests/test_s69_w2_pins.py + tests/test_s77_w2_pins.py solo;
   green.
5. notes.md REQUIRED: the old and new digests, the install receipt,
   the plugin list output.

## Bounds
- One token in one file, the manifest digest line, nothing else.
  If the gate still refuses, stop honestly with the verbatim error.
