# s106 w1 — the pack digest check; the epic extends

The resume's maintenance season. Your lane: the pack digest checked
fresh (probe, don't trust), the board-arc epic extended with s100
(preserving every verdict).

## Ground truth (measured 2026-09-18)
- the installed pack: kancil-base @ a22944c1 (the s96 sync); the
  draft: probe fresh — the draft re-sealed at s88 (the correctness
  prior) and s94 (the governance templates): verify, never trust
- .rumpun/epics.yaml: board-arc carries s69-s96 (the s97-s100
  seasons: closed after the extensions stopped keeping pace)
- the pinned arithmetic: the two epic views sum to the whole ledger

## Task
1. The pack digest check: probe the draft digest fresh; reinstall
   digest-verified if it differs from the installed copy; record the
   equality if not.
2. Extend the board-arc epic: epics.yaml gains s97-s100 (verify
   which seasons the campaign epic holds first; move accordingly).
   Preserve every verdict (the pinned arithmetic).
3. Verify: the epic view sums to the whole ledger; lint passes.
4. notes.md REQUIRED: the digests, the epic view, the arithmetic.

## Bounds
- Edits: .rumpun/epics.yaml only. Reinstall only if the digest
  differs. notes.md REQUIRED.
