# s18 w1 — finish H1 + H6 from the s17 salvage; warning-transition fix

You are w1 in season s18 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/engine.py, src/rumpun/akar.py, akar
record codex-review-2026-09-14 (H1 + H6 with reproductions), and the s17
salvage draft .rumpun/akar/evidence/s17/w1-akar.py (a 72-line parse-clean
H6 start from the season the budget killed — audit it before reuse). Use
your FILE TOOLS; no nested-heredoc scripts. You have 40 minutes.

## Deliverables (write ONLY inside your workspace; the harness merges)

1. engine.py + akar.py patched copies + notes.md (anchors + verification).

## H1 — _finalize holds state.lock across the whole transaction

Same spec as s17: lock held across terminal-state check, ownership
snapshot, termination, and final write (pass the lock into _save_state).
No nesting: _finalize_agent_stream derives its own flock — call it before
acquiring or restructure. The reviewer's repro: stop racing a spawn left
an agent live and untracked.

## H6 — akar append serializes duplicate-check + publication

Finish the s17 draft: one flock on akar/append.lock across duplicate
check, existence check, atomic publish; unique (pid-based) temp name;
publish refuses existing targets; body bytes unchanged. First-use lock
creation via a+ open.

## Warning-transition fix (observed live in s17)

engine's _mark_file_tools logs one WARNING per file-tool sighting — s17
logged ~30 for two writers. Fix: warn only on the false->true transition
(when meta["file_tools"] is not already True). Keep the lane-event +
marking behavior; offset/mark logic untouched.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch lint.py (w2 owns it), cli.py, report.py, audit.py, tests/.
- Existing caller signatures unchanged; never log token values or content.

## Verify before finishing

Repro both review scenarios against your patched copies (stop-race: zero
live untracked agents; same-id append: exactly one success) and count
warnings across a multi-sighting synthetic stream (expect 1). Run the
suite (70 tests) in a scratch tree. All three results in notes.md.
