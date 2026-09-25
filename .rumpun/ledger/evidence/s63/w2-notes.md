# s63 w2 — notes

## Contract pinned (spec-first; w1 owns tools/)
1. Runtime-framed file token ("writes results.jsonl") with the artifact
   in the campaign runs state .rumpun/runs/<sid>/: clause MATCH, exit 0
   VERIFIED, evidence records the classification.
2. Ghost committed-file claim: DELTA exit 1, missing file named in the
   record. The no-bailout guard.
3. Evidence names each file-shaped token's classification:
   runtime-checked vs committed-tree claim.

## Pins
.rumpun/runs/s63/w2/tests/test_s63_w2_pins.py — 312 lines, 3 subprocess
pins, S63W2_TIMEOUT = 240s per checker subprocess, throwaway git-repo
closes under tmp_path (src, one green pin, DESIGN.md row, the runtime
artifact worktree-only), helpers _s63w2_-prefixed, additions-only.

## Measured red set
Run A — vs the season-start checker (git show HEAD:tools/artifact_check.py
into /tmp/s63w2_base; repo @ 6cce2f9, pre-s63):
2 failed, 1 passed, exit 1. Log: /tmp/s63w2_base_red.log
- pin 1 FAIL: "the runtime-framed clause DELTAs ... : DELTA; missing
  file: results.jsonl" — the check-s61 false positive, reproduced.
- pin 3 FAIL: "runtime clause DELTA ... missing file: results.jsonl;
  file src/rumpun/finalize.py exists" — no classification named.
- pin 2 PASS — the no-bailout guard holds pre-existing, by design.

Run B — vs the live tree: w1's classifier had already landed
(tools/artifact_check.py modified in the worktree, uncommitted,
+136/-9 vs HEAD at measurement time).
- first pass: 2 failed, 1 passed — pins 1 and 3 red for a FIXTURE
  reason, not the spec reason: I had placed the artifact at
  <proj>/runs/<sid>/ (repo root); the landed checker binds the campaign
  runs state at .rumpun/runs/<sid>/. My fixture misread the convention.
- after correcting the fixture to the campaign convention (artifact
  worktree-only, uncommitted — the repo gitignores .rumpun/runs):
  3 passed, exit 0. Log: /tmp/s63w2_live.log

## Surface assumptions
- Evidence assertions need the token plus "runtime" (runtime clauses) or
  "committed" (committed clauses) in the evidence cell. The landed
  rendering satisfies both: "runtime artifact <token> PRESENT
  (runs/<sid>/...) (runtime-checked against runs/<sid>/)" and "file
  <path> exists (committed-tree claim)".
- Runtime resolution binds the live <repo>/.rumpun/runs/<sid>/; the
  fixture mirrors the real repo, where .rumpun/runs is gitignored and
  worktree-only.
- Runtime framing triggers per w1's diff: "writes <token>", a
  runs/<sid>/ prefix, or a close-time cue; a missing runtime artifact
  DELTAs exactly like a missing committed file.

## Floor
- ruff clean (0.14.10, --no-respect-gitignore, line-length 100);
  py_compile ok; 3 tests collect; _s63w2_/S63W2_ prefixes collide with
  nothing in tests/ (grep).
- Repo tests/ untouched: git status shows only tools/artifact_check.py
  (w1), .rumpun/RESUME.md, and the untracked check-s62 ledger record.
- Merge expectation: pins green at merge — measured against the landed
  classifier (Run B, corrected), 3 passed exit 0.
