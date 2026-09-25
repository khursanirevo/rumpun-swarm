# s107 w2 — the pack digest check; the composer render; the inventory

The maintenance rhythm's other half: the pack digest checked fresh,
the composer rendered over the ledger, and the honest inventory of
what remains.

## Ground truth (measured 2026-09-18)
- the installed pack: kancil-base @ a22944c1 (the s96 sync); the
  draft: probe fresh — it may have moved at s88/s94 (the templates)
- the composer: the label split + the spend lines render over the
  ledger (the s95 w1 landing; the s96/s104 w2 renders are the
  precedents)
- the board: the open set unchanged (see above)

## Task
1. The pack digest check: probe the draft digest fresh; reinstall
   digest-verified if it differs from the installed copy; record the
   equality if not.
2. The composer render fresh over the ledger: the label split + the
   spend lines render. notes.md carries it.
3. The inventory: what remains, named honestly — the operator-gated
   fronts, the standing standards, any thin items that name
   themselves. notes' deliverable.
4. notes.md REQUIRED: the digest check, the render, the inventory.

## Bounds
- Read-only on the tree except notes.md. Reinstall only if the digest
  differs. notes.md REQUIRED.
