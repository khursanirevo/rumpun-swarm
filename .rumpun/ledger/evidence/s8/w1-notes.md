# s8 w1 — evolve approve/reject

Deliverables in this workspace: `evolve.py`, `cli.py` (full copies of
`src/rumpun/` at commit `29f449f` plus the changes below), `lane_tool.py`,
this note. Repo untouched; merge is a harness step.

## Contract

| Verb | Function | Effect |
|---|---|---|
| `rumpun evolve approve FILE` | `evolve.approve_draft(root, drafted) -> Path` | append akar `approve-<sid>`; draft never modified |
| `rumpun evolve reject FILE` | `evolve.reject_draft(root, drafted) -> Path` | move draft to `musim/rejected/<name>`; append akar `reject-<sid>` |

Validation (both verbs): draft loads via `yamlio`; `id` matches `s<N>`.
`EvolveError` on parse error, non-`s<N>` id, or missing file (wraps `OSError`).

- `approve-<sid>`: title `season <sid> approved`. Body: operator approved at
  autonomy stage manual; the draft's goal line; the citations
  `methodology.evidence` names, comma-joined — `none` when empty/missing.
- `reject-<sid>`: title `season <sid> rejected`. Body: P33 `on_reject` —
  action `rollback_to_last_good`, pause true, escalate_after
  consecutive_rejects 2 — and manual stage means the operator pauses the
  chain.
- Reject order: check target collision → mkdir `musim/rejected/` →
  `Path.replace` → append record.
- CLI: both verbs `logger.info` the record path, return 0. `EVOLVE_STUBS`
  keeps only `rollback`. Docstring version note v0.8.0; Implemented line
  gains evolve approve/reject.
- `akar.AkarError` wraps into `EvolveError` in both verbs (double-approve /
  double-reject exits 1 with a clean message, not a traceback).

## Verification (✅ verified real, 2026-09-14)

- `ruff check` clean on all three files (repo config: line-length 100, py3.10).
- 21/21 tests pass with workspace `evolve.py`/`cli.py` overlaid on a copy of
  `src/rumpun` (`PYTHONPATH` overlay; repo files untouched), `pytest -q`.
- Behavior smoke (overlay import, tmp project): approve body carries
  stage/goal/evidence + `none` fallback; draft bytes unchanged after approve;
  reject moves the file and writes the P33 body; duplicate record id, reject
  target collision, bad id, and missing file each raise `EvolveError`.
- CLI e2e exit codes: approve 0, duplicate approve 1, reject 0, re-reject 1
  (moved), rollback 2 (stub intact). `evolve --help` lists
  `{plan,apply,approve,reject,rollback}`.

## Flagged

1. `ruff check <dir>` on this workspace reports nothing: `.rumpun/rimba/` is
   gitignored and ruff respects gitignore. Check by explicit file paths.
2. `__init__.__version__` and `pyproject.toml` still say 0.7.0; only the cli
   docstring says v0.8.0. Harness bumps both at merge (s3/s5/s7 precedent).
3. Reject moves the draft before appending the record (spec order). If the
   append then fails, the draft is already in `musim/rejected/`; recover by
   moving it back. The error names the record id.
4. `python -m rumpun` swallows exit codes: `__main__.py` calls `main()`
   without `sys.exit`, so every `-m rumpun` invocation exits 0. Pre-existing,
   outside this task's file set. Fix at merge: `sys.exit(main())`.
5. `cli.main` catches no `akar.AkarError`; `harvest` still tracebacks on a
   duplicate record id. Pre-existing, untouched. Issue draft (khursani8/
   khursanirevo): "rumpun: `python -m rumpun` exits 0 on error — `__main__.py`
   must `sys.exit(main())`; also catch `akar.AkarError` in `cli.main` so a
   duplicate harvest record exits 1 instead of tracebacking."

## Lane (protocol v2, non-blocking)

- `lane_tool.py (kind, text)` appends `{"from": "w1", "kind", "text"}` via
  `rumpun.collab.append_event` from `RUMPUN_LANE_FILE`/`RUMPUN_LANE_LOCK`;
  `("read", "")` prints events. Posted: start, policy (verb contract), done.
  No waits on w2 at any point.
