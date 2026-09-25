# s19 w1 — H2 identity-checked termination + H3 workspace cwd

You are w1 in season s19 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/engine.py, and akar record
codex-review-2026-09-14 (findings H2 and H3 with the reviewer's
reproductions). FILE TOOLS directly; no nested-heredoc scripts. 40 minutes.

## H2 — _terminate re-checks process identity before signaling

Today: _terminate(ws, pid) signals killpg(pid) with no proc_start check; a
recycled pid means an innocent process group is killed. It also receives no
identity context. Fix: callers pass the recorded proc_start; _terminate
re-checks _proc_start_ticks(pid) == proc_start (when recorded) before the
first signal; on mismatch log a WARNING (path + pids, no content) and skip
signaling. Finalize's kill loop passes identity from state["spawned"].
Review's second half (crashed leaders leaving descendants) is out of scope
unless trivial — otherwise note it for a later season.

## H3 — agents run inside their workspace

Today: Popen sets no cwd, so the workspace is convention only (the
reviewer's pwd route printed the repo directory). Fix: resolve the
workspace path before spawning and pass cwd=ws to Popen. Route commands
that assumed repo cwd (cat {prompt} with absolute paths) must keep
working — check every route shape in rumpun.yaml and the scaffold; use
absolute paths in the wrapper where needed (the exit-file printf already
uses an absolute path).

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch lint.py, akar.py (w2 owns citation enforcement there),
  cli.py, report.py, audit.py, tests/.
- Existing caller signatures: _terminate may gain a required param — update
  ALL internal call sites; no behavioral regression in the 84-test suite.

## Verify before finishing

Repro both: (1) a stub agent whose pid slot gets recycled (simulate by
passing a wrong proc_start) is NOT signaled and logs the mismatch warning;
(2) a pwd route writes its cwd into agent.log and it equals the workspace.
Suite green (uv run pytest, 84 tests) against patched copies in a scratch
tree. Both repro outputs in notes.md.
