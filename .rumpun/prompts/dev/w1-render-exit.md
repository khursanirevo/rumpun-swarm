# s22 w1 — M1 deterministic running-season renders + M5 exit honesty

You are w1 in season s22 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/report.py, src/rumpun/engine.py (the
TERMINAL/finalize path + cli exit mapping), and akar record
codex-review-2026-09-14 (M1 + M5). FILE TOOLS directly. 40 minutes.
WRITE ONLY inside your workspace (the s21 writers broke that rule; do not).

## M1 — reports render from persisted state only

Today report calls read_status, which recomputes snaps from /proc and
clocks for RUNNING seasons — identical bytes, different pages, and the
footer's self-identifying state hash covers bytes the page does not
reflect. Fix: report renders from the PERSISTED state.json for every
season (running included); workspace links sort deterministically
(sorted rglob); the footer hash keeps hashing exactly the bytes the page
rendered from. The landing page's live freshness comes from the state
hook's frequent re-renders, not from /proc reads inside a render.
cli.py needs a read_status-vs-persisted split? If cli season status
must stay live, add engine.read_persisted_status and have report use
it — cli untouched if possible.

## M5 — failed agents produce honest exits

Today any all-terminal snapshot finalizes completed and every cli path
exits 0. Fix: finalize distinguishes completed (all exited 0) from
failed (>=1 failed/crashed) as the recorded status suffix or a new
additive status field, and the season verbs map stopped_budget /
stopped_stall / failed to nonzero exits. Keep the akar/report/audit
contracts reading status values they already know (additive field
"exit_honest": true only if needed). Document the mapping.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch collab.py (w2 owns it), lint.py, akar.py, evolve.py,
  cli.py unless the exit mapping cannot live in engine (then minimal,
  documented). tests/ is w2's.
- The 103-test suite stays green.

## Verify before finishing

Repros: render a running season twice with a monkeypatched clock —
byte-identical; unsorted-link fixture renders sorted; a both-fail
season records its status and the verb exits nonzero. Suite green
against patched copies. All in notes.md.
