# s28 w1 — README to current truth

You are w1 in season s28 (repo root: the parent of this .rumpun tree). Read
README.md (stale at v0.9.0), DESIGN.md (sections 13-15 + the season table),
pyproject.toml (0.11.0), src/rumpun/cli.py (the verb surface), and akar
records audit-13 through audit-16. FILE TOOLS directly. WRITE ONLY inside
your workspace. 40 minutes.

## Deliverable: README.md rewritten to current truth (workspace copy)

Every verb implemented and verified: init, lint, graph, models, direct,
board, harvest, audit [--last N], season start/status/list/stop/report/
show, evolve plan/apply/approve/reject/rollback. Plus the tools:
tools/replay_corpus.py (the cross-season regression gate) and
tools/render_dashboard.py (the maintained render loop). Plus the
self-evolution loop itself: season -> harvest -> audit -> seed, evidence
citations required, candidates capped, never auto-applied.

Structure (DTS: answer first, bullets for anything enumerable):
- What rumpun is (one paragraph, plain sentences).
- Quickstart (init -> write a season -> lint -> start -> harvest -> audit).
- The verb table (verb | what it does | one honest caveat where relevant).
- The self-evolution loop (how a season is proposed, judged, and reflected
  on; the corpus gate; what the dashboard shows).
- Version: 0.11.0.
Honesty rules: no claimed-but-unverified features; every caveat from the
season records that survives (running-season report snapshots, the mtime
estimate for history-less callers, detection refines never gates) stays.

## Constraints

- Do not modify DESIGN.md (w2 owns it), src/, tests/, tools/.
- Markdown, no HTML; no marketing adjectives.

## Verify before finishing

Every cli verb you document exists in cli.py --help output (paste the
help into notes.md). Version strings match pyproject. notes.md lists
each claim you could NOT verify, if any.
