# s14 w2 — spec-first tests for the spawn tool-check

You are w2 in season s14 of the rumpun campaign (repo root: the parent of
this .rumpun tree). Read DESIGN.md sections 13 and 15, src/rumpun/engine.py
(watch cycle + snap finalize), and akar records glm-toolless-spawn and
audit-2. Do NOT implement the detector — w1 owns engine.py. You own the
test contract, spec-first: your new tests are expected to FAIL against
current code and PASS once w1's patch lands.

## Deliverables (write ONLY inside your workspace; the harness merges)

1. tests/test_rumpun.py based on the current repo file (50 tests, all
   kept; insertions plus minimal fixture helpers only — diff must show
   additions, no rewrites).
2. notes.md — what each test pins and why; run evidence.

## Contract to pin (from the s14 season yaml + akar audit-2)

1. `log_signature_toolless(text: str) -> bool` exists in rumpun.engine,
   pure, and classifies synthetic logs: the tool-less signature present ->
   true; a clean boot log -> false; empty -> false; whitespace-only ->
   false; signature plus surrounding clean content -> true.
2. Watcher integration: a snap whose agent.log grows the signature gets
   snap["toolless"] = true in _season/state.json; it is never unset; the
   snap still finalizes by the existing rules afterwards. Use the existing
   engine test fixtures/patterns for spawning (see the dual-start test and
   the lock tests) with a stub route command that writes the signature
   into its agent.log.
3. Additive-key safety: a state.json carrying "toolless" marks renders
   through rumpun.report unchanged (existing render test pattern) and
   run_audit's F4 outcome counts do not change because of the mark.
4. No new polling: assert the detector hook is invoked from the existing
   watcher cycle (structure-level check is fine — e.g. the watcher calls
   the classifier per live agent; do not require wall-clock timing).

## Constraints

- logging, never print; ruff check clean (line-length 100); py3.10+.
- Do not modify src/ or cli.py. tests + notes.md only.
- Never include API keys or token values in anything you write.
- ruff --no-respect-gitignore on your files (rimba/ is gitignored).

## Verification before you finish

Run your file against CURRENT code: state the expected red set (the new
tests) in notes.md. The harness re-runs the suite after merge; 50 green +
new green is the s14 gate.
