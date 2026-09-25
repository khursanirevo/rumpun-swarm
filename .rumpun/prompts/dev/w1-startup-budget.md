# s19 season taught: repro-first, 40 minutes, file tools directly

You are w1 in season s20 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/engine.py, and akar record
codex-review-2026-09-14 (findings H5 and H9 with reproductions). FILE TOOLS
directly; no nested-heredoc scripts. 40 minutes.

## H5 — a failing startup must not abandon live children

Today: route resolution happens inside the spawn loop; a missing second
route raises EngineError after the first child is already running — with no
watcher, unregistered if the crash precedes the spawned-map save (reviewer
reproduced). Fix in layers:
1. Validate ALL benih before any spawn (routes resolve, prompts exist,
   lanes preparable): raise before the first Popen.
2. Wrap the spawn loop: on any failure, terminate already-spawned children
   via the existing _terminate (identity-checked), record the error in
   state, and re-raise.
3. Persist spawn intent BEFORE Popen (write the child's entry into
   state["spawned"] under the held lock first, save, then spawn), so a
   crash between Popen and save still leaves a registered, killable child.
Keep the single-flock discipline (no nested locking; reuse the held
state_lock for intermediate saves like the existing loop does).

## H9 — per-agent budgets enforced individually

Today: _stop_rules takes max(minutes) as the whole-season budget_s and one
watcher deadline covers everyone. Fix: the watcher computes each live
agent's own deadline from its benih budget; an agent past ITS deadline is
terminated (via _terminate) and its snap marks terminated_budget (state
"terminated" is fine — add the reason to notes if a new key is cleaner;
additive only). The season ends completed when every agent reached a
terminal state (naturally or budget-stopped). campaign_cost_cap stays a
flag (P9) — do NOT build a meter (out of scope).

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch lint.py, akar.py, evolve.py (w2 owns lifecycle there),
  cli.py, report.py, audit.py, tests/.
- Existing caller signatures preserved where possible; update internal
  call sites as needed; the 94-test suite must stay green pre-merge
  except for w2's expected new reds.

## Verify before finishing

Repros: (1) two-benih season whose second route is missing — first child
terminated, error recorded, no live untracked process; (2) a crash-style
failure between spawn and save (monkeypatched _save_state) — the child is
still registered and killable; (3) two agents with 1-minute and 30-minute
budgets (use seconds-scale stubs for test speed) — the short one is
terminated at its own deadline, the long one completes. Suite green
against patched copies. All three outputs in notes.md.
