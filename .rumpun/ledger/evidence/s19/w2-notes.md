# s19 w2 — H7 digest enforcement in lint.py; H2/H3/H7 pinned spec-first

## Anchors

- Codex review: `.rumpun/akar/evidence/codex-review-2026-09-14/review-full.txt`
  — H2 at :6508, H3 at :6510, H7 at :6518 (repeated in the summary at
  :6567/:6569/:6577).
- w2 lint.py copy: `.rumpun/rimba/s19/w2/lint.py` — three hunks vs the repo
  file (diff-measured): `import hashlib` at 9a10, `from rumpun import akar,
  yamlio` at 16c17, and `_citation_resolves` replaced in full
  (146a148,157 + 150,152c161,164 + 154,157c166,184).
- Tests: `tests/test_rumpun.py` — additions-only vs the repo file:
  0 removed, 192 added (diff-measured). 10 new tests.
- New test anchors (workspace file): section header :1874; H7 pins :1893
  matching digest, :1901 tampered digest, :1911 tampered record body, :1926
  8-char prefix, :1934 too-short digest, :1944 partial id; H2 pins :1968
  matching signals, :1991 mismatched spares + warns, :2018 None never
  signals; H3 pin :2055 workspace cwd.

## H7 spec as landed

Citation `akar:<id>@<digest>` resolves only when:

- the exact record is declared in akar/ — resolved with `akar.find_record`
  (the same declared-id scan akar itself uses; no substring ids), and
- the cited digest matches the record's recorded body digest: full 64 hex
  chars or a unique prefix of >= 8 (the citation regex floors at 8).

Recomputation follows akar.append_record's layout: body =
"\n".join(lines[4:-1]), digest = sha256 of the utf-8 body bytes, recorded on
the final "sha256: " line. A record with no sha256 line fails closed with a
logged warning. The lint error message keeps its existing shape and names
the citation verbatim.

## Pinned specs for w1 (engine.py)

- H2 call shape: `engine._terminate(ws, pid, proc_start)`. Recorded ==
  live proc_start: signal (existing terminated-marker + killpg flow).
  Recorded != live, or recorded None: no signal; a rumpun.engine WARNING;
  the stub is alive after the call. Stubs trap SIGTERM by touching a
  marker; sleep 60 shares the process group, so killpg ends it at once and
  the shell runs the trap immediately — no wall-clock waits in the pins.
- H3: the spawn Popen sets cwd=<workspace>. The pin runs the reviewer's
  pwd repro through start_season and asserts pwd's output resolves to the
  workspace.

## Measured red set (current repo code + this test file, scratch tree)

Scratch tree: repo `src/` + this test file. Command:
`PYTHONPATH=src python -m pytest tests/test_rumpun.py -q -p no:cacheprovider`.
Final file, warm-cache run: `7 failed, 85 passed, 2 skipped`, pytest exit 1.

| expected red | evidence |
|---|---|
| `test_lint_citation_tampered_digest_is_error` (H7) | "lint accepted a tampered digest" — the substring scan resolves a wrong hash |
| `test_lint_citation_tampered_record_body_is_error` (H7) | same mechanism: an altered body still substring-resolves |
| `test_lint_citation_partial_id_is_error` (H7) | "lint accepted a partial id" — a substring id resolved |
| `test_terminate_matching_proc_start_signals` (H2) | TypeError: _terminate() takes 2 positional args — the behavioral red lands with w1's patch |
| `test_terminate_mismatched_proc_start_warns_and_spares` (H2) | TypeError (same signature gap) |
| `test_terminate_none_proc_start_never_signals` (H2) | TypeError (same signature gap) |
| `test_engine_spawns_agent_inside_workspace_cwd` (H3) | pwd printed the caller's cwd, not the workspace |

H7 accept shapes (matching digest, 8-char prefix, too-short digest) pass
against current code — regression guards, not reds. The 2 skips are the s16
real-stream replay (fixture exists only in the repo clone); they pass in the
repo tree.

Cold-cache caveat, measured: the L2 dual-start transient hits in cold runs —
`test_dual_start_single_spawner` failed in 3/3 red-tree runs that ran first
on a cold cache (failure: "ERROR season s1 already finished (completed); use
a fresh id" — starter 2 arrives after starter 1 completed the season; review
L2) and passed in every warm run (green tree 3/3, red warm 1/1, repo 2/2).
Run scratch suites solo and warm; treat cold-run extras as flake candidates
and re-run before recording a red set.

## Verification (all measured this session)

- Baseline: repo tree, `84 passed`, exit 0 — measured twice (session start
  and after all edits).
- Additions-only proof: diff repo vs workspace test file → 0 removed,
  192 added.
- lint.py patch proof: diff repo vs workspace copy → the three hunks above,
  nothing else.
- Red tree (repo code + new tests), warm: `7 failed, 85 passed, 2 skipped`
  — exactly the table above; every baseline test passes modulo the 2
  environment skips.
- Green tree (workspace lint.py + new tests): `4 failed, 88 passed,
  2 skipped` — the 4 are w1's H2 x3 + H3; all 6 H7 pins pass with my
  lint.py.
- Real-tree citations: patched-lint CLI over all 20 `musim/s*.yaml`:
  s1-s19 exit 0 (every citation resolves, including s19.yaml's three
  full-digest citations); s20 exits 1 as a pre-existing incomplete draft
  (4 empty primary_change errors, zero citation findings).
- Ruff: `ruff check --no-respect-gitignore` on both workspace files → All
  checks passed! (the flag is required: rimba/ is gitignored, otherwise
  ruff checks zero files). Ruff caught 3 real F821s (missing
  `import signal`) in my first draft; fixed pre-delivery.
- Byte-exactness: both workspace files diff-verified against the repo
  originals after every write (harness-write-corruption protocol).

## Handoff to w1 / harness

- lint.py: apply the three-hunk patch (workspace copy is merge-ready).
- engine.py: land H2 with the pinned call shape (mismatch or None → spare +
  one WARNING; match → signal, existing flow) and H3 (Popen cwd=workspace).
- After w1 lands and the harness merges: repo tree expected `94 passed`
  (84 kept + 10 new); scratch `92 passed, 2 skipped`.
