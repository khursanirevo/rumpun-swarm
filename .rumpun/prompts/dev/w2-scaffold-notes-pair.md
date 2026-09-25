# s134 w2 — the scaffold asks for the notes; shipped directives get marked (issues #46 and #48)

Two filed defects on the lifecycle's ends: the scaffold never asks for
what the gate demands, and shipped directives never leave pending.

## Ground truth (measured 2026-09-20)
- issue #46: the close gate demands run-dir notes.md but the
  scaffolded writer prompts never ask writers for it - the s112 gate
  was built after the scaffold; the prompts never caught up.
- issue #48: directives.jsonl status stays pending forever - shipped
  directives never marked (the s133 board read named the same gap on
  the assessments).
- the surfaces: the scaffold's writer prompt templates
  (src/rumpun/scaffold.py, prompts/base/), the directives reader in
  src/rumpun/evolve.py or the loop, directives.jsonl's row shape
- the honest mark: a directive ships when its named work is verifiably
  in the tree (the campaign reads the evidence, not the request)
- fixture discipline: tmp campaigns; the real directives.jsonl never
  written in tests

## Task
1. Fix both: the scaffolded writer prompts ask for notes.md (the gate
   and the prompts agree); directives.jsonl gains the shipped marking
   (a directive whose named evidence exists in the tree reads shipped,
   surfaced at plan or loop time). Pins red-first in
   tests/test_s134_scaffold_notes_pair.py (tmp campaigns).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/scaffold.py, src/rumpun/evolve.py or
  src/rumpun/loop.py (the directives marking),
  tests/test_s134_scaffold_notes_pair.py only. notes.md REQUIRED.
