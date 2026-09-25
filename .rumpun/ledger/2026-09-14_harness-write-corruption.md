# akar record: harness-write-corruption
id: harness-write-corruption
date: 2026-09-14
title: harness heredoc writes produced fabricated YAML twice on 2026-09-14
Two harness writes of musim state files (s3.yaml, s4.yaml) came out with
content never intended: invented keys (on_reject inside a benih entry,
route: nonexistent-route, primitive: fals junk), corrupted values
(fansion.yaml, budget minutes 0, agent: rank_gaps, reads: fansion.yaml).
Lint caught the structural breaks; value-level fabrications passed structure
until the DAG read or manual readback. Nothing corrupted was spawned: both
files were rewritten and read back in full before gate/spawn.

Mitigation now standing (see memory: verify-state-writes): after every
heredoc write of tracked state, cat the full file in the same command and
check against intended content before lint/apply/spawn.
sha256: f86a5b80b229a582cfc5a2c2a6ffca0374de160876e9458e9388e9e7ad46cd7e
