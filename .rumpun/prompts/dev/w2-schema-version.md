# s68 w2 — schema versioning: the campaign reads its own age (directive seq 6)

.rumpun must survive its own structural change: version the schema,
document it, and make readers refuse what they cannot read.

## Ground truth
- s67-harvest@704ae8de: the kancil route, kancil-base pack, competition
  template landed; suite 291/291.
- The s54 rename kept benih: as a back-compat read — the precedent for
  versioned reads.
- audit-42 F6 flags drift between docs and behavior; version skew is the
  same class.

## Task (spec-first, pins in tests/test_s68_w2_pins.py, _s68w2_ prefix)
1. Pin: every campaign scaffold (rumpun new / rumpun init) writes
   `schema: 1` at the top of rumpun.yaml; existing campaigns without the
   key read as version 1 (default), never refuse.
2. Pin: a campaign whose rumpun.yaml carries `schema: 99` refuses the
   next mutating verb (season start, evolve apply) with an error naming
   the supported range and pointing at .rumpun/CHANGELOG.md. Read-only
   verbs (kanban, status, lint) still work.
3. Pin: .rumpun/CHANGELOG.md exists after init, records schema versions
   newest-first with one line per version, and is prunable with RESUME.md
   (same prune discipline, every 5 schema bumps).
4. Implement: scaffold writes schema + CHANGELOG; loader reads default 1;
   mutating verbs check; kanban gains no new cards (the refusal message
   is the surface).

## Bounds
- The benih back-compat read stays. No format migration in this season —
  version 1 IS today's format; the refusal path is the deliverable.
- Budget 40 minutes; the known suite classes are the floor.
