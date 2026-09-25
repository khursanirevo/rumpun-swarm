# s9 w1 — evolve rollback

Deliverables in this workspace: `evolve.py`, `cli.py` (full copies of
`src/rumpun/` at commit `48a2d10` plus the changes below), `lane_tool.py`,
this note. Repo untouched; merge is a harness step.

## Contract

| Verb | Function | Effect |
|---|---|---|
| `rumpun evolve rollback SID` | `evolve.rollback_season(root, sid) -> Path` | move `musim/<sid>.yaml` to `musim/rejected/<name>`; append akar `rollback-<sid>` |

Reject contains a DRAFT (pre-apply); rollback contains an APPLIED season
(a `musim/<sid>.yaml` that passed apply and may have run) — harness decision,
kept symmetric with reject.

- SID, not FILE: sid must match `s<N>` or `EvolveError` (passing
  `musim/s1.yaml` lands here too, by design).
- `musim/<sid>.yaml` must exist, else `EvolveError` whose message hints
  `rumpun evolve reject` for drafts that were never applied.
- `rollback-<sid>`: title `season <sid> rolled back`. Body: P33 `on_reject`
  — action `rollback_to_last_good`, pause true, escalate_after
  consecutive_rejects 2 — plus: code-level restore is an explicit git
  revert by the operator; git history is the evolution ledger; the verb
  never runs git.
- Order: sid check → existence check (hint) → target collision check →
  mkdir `musim/rejected/` → `Path.replace` → append record.
- `akar.AkarError` (duplicate id) wraps into `EvolveError`: double rollback
  exits 1 with a clean message, no traceback.
- CLI: root from cwd (id-verb precedent: season status/stop), `logger.info`
  the record path, return 0.

### EVOLVE_STUBS decision

Dropped outright — the dict and the `for ... in EVOLVE_STUBS.items()` loop —
not guarded with `if EVOLVE_STUBS:`. The P36 D9 registry is now empty: every
designed verb exists, and an empty-but-present stub loop reads as expecting
more stubs. `NOT_IMPLEMENTED` / `SEASON_STUBS` stay untouched (both empty,
out of this task's file semantics). The cli docstring line "Everything else
prints an explicit not-implemented notice and exits 2." went vacuous with
the registry and now states the registry is empty; unknown verbs exit 2
(argparse, unchanged behavior). Docstring version note v0.9.0; Implemented
line gains evolve rollback.

## Verification (✅ verified real, 2026-09-14)

- `ruff check` clean on all three files by explicit path (repo config:
  line-length 100, py310).
- 24/24 tests pass with workspace `evolve.py`/`cli.py` overlaid on a copy
  of `src/rumpun` (`PYTHONPATH` overlay in /tmp; repo files untouched),
  `pytest -q`, 1.30s.
- e2e smoke, 34/34 checks, real `python -m rumpun` subprocesses on /tmp
  projects: happy path exit 0, season moved byte-identical, record carries
  id/title/P33 body/git line; missing season exit 1 with the reject hint;
  bad sid (`s1x`, `musim/s1.yaml`, `s`, `s01a`) exit 1; target collision
  exit 1 with nothing moved; duplicate record id exit 1 wrapping
  `AkarError`; `evolve --help` lists rollback, no stub wording; missing
  argument and unknown verb exit 2.
- One corrupted write caught before gating: `cli.py` line 61 lost a closing
  quote in transcription (ruff caught it); a full `diff -u` against the repo
  originals then confirmed the only deltas are the intended ones.

## Flagged

1. `.rumpun/rimba/` is gitignored, so `ruff check <dir>` reports nothing —
   check by explicit file paths (s8 flag, still true).
2. `__init__.__version__` and `pyproject.toml` still say 0.8.0; only the
   cli docstring says v0.9.0. Harness bumps both at merge (s3/s5/s7/s8
   precedent).
3. Move-before-append ordering inherited from reject: if the akar append
   fails after the move (e.g. duplicate `rollback-<sid>` from an earlier
   partial run), the season file already sits in `musim/rejected/`; recover
   by moving it back. The error names the record id. Spec order, kept for
   consistency with reject.
4. No latest-season constraint: any existing `musim/s<N>.yaml` can roll
   back (s2 while s3 exists). The spec names existence only; `draft_next`
   keeps the latest invariant. Deliberate non-constraint.
5. Rollback does not touch season runtime state: a running season keeps
   running (`season stop` is the operator's separate verb) and
   `rimba/<sid>/` state stays as-is. Containment here is YAML + ledger,
   per spec.
6. Observed, not this lane's doing: `.rumpun/musim/s10.yaml` appeared in
   the repo untracked at 17:44:02 — harness-side next-season draft written
   at s9 seed time, before this lane's first write (17:47). Left untouched.

## Lane (protocol v2, non-blocking)

- `lane_tool.py (kind, text)` appends `{"from": "w1", "kind", "text"}` via
  `rumpun.collab.append_event` from `RUMPUN_LANE_FILE`/`RUMPUN_LANE_LOCK`;
  `("read", "")` prints events. Posted: start, policy (verb contract),
  done. No waits on w2 at any point. w2's start (seq 0, spec-first
  rollback tests) was read as evidence only.
