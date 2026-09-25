# s17 w1 — finalize locking (H1) + akar append serialization (H6)

You are w1 in season s17 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/engine.py, src/rumpun/akar.py, and the
akar record codex-review-2026-09-14 (the external review; your scope is its
findings H1 and H6, including the reviewer's reproductions). Use your FILE
TOOLS directly; no nested-heredoc patch scripts.

## H1 — _finalize must hold state.lock across the whole transaction

Today: _finalize reads state (_load_state), terminates agents, then saves —
no lock across the sequence; a concurrent starter can add agents after the
terminal snapshot, leaving them live and untracked (reviewer reproduced:
stopped_operator omitted a spawned name and left it alive).
Fix per the review: hold _state_lock(root, sid) across the terminal-state
check, the ownership snapshot, termination, and the final write. Pass the
held lock into _save_state(root, sid, state, lock_file=...) — the parameter
exists (start_season uses it). Mind the no-nesting hazard documented in
_scan_agent_stream: _finalize must not call helpers that flock the same
lock while it is held. _finalize_agent_stream derives its own lock — call
it BEFORE acquiring, or refactor carefully.

## H6 — akar append must serialize duplicate-check and publication

Today: append_record checks _declared() then final.exists() then writes;
no lock; the reviewer reproduced two same-id appends both succeeding, the
second body replacing the first. Fix: one lock file (akar/append.lock,
flock) held across duplicate-check, existence check, and atomic publish;
use a unique temp name (pid-based) so two writers cannot share it; publish
refuses an existing target (keep the AkarError contract). Lock file
creation must be safe on first use (a+ open), and the record body format
is unchanged byte-for-byte.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch lint.py (w2 owns it), cli.py, report.py, audit.py, tests/.
- Additive behavior only: existing callers' signatures unchanged.
- Never log token values or stream content.

## Verify before finishing

Write your patched copies (engine.py, akar.py) in this workspace, plus a
repro script mirroring the reviewer's: a stop racing a spawn (slow stub
route + stop_season in a thread) proves zero live untracked agents; two
processes (or threads under a barrier) appending the same record id prove
exactly one success. Run the suite (uv run pytest, 70 tests) against your
patched copies in a scratch tree. Put both repro outputs in notes.md.
