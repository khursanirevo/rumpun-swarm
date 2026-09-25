# s59 w1 notes — the close check reads the fresh row

Shipped and verified. `ships_row` in tools/artifact_check.py gains the
close-time fallback: no extracted row plus a live worktree row means the
checker uses the live row and records the disclosure line in the check
record; both present means the extracted row wins with no disclosure;
neither means the refusal still names the sid. Tamper detection is
untouched: files, pack digests, and harvest seals bind to the extracted
tree exactly as before.

## What changed (workspace copies; the harness merges)

- `tools/artifact_check.py` — additive: `LIVE_ROW_NOTE` constant (the
  verbatim disclosure line), `_row_lines` helper, `ships_row(design, sid,
  live_path=None)` returning a third element (the row source note), a
  `ships_source` field on `CheckResult`, the disclosure line in
  `build_record`, the `main()` caller passing `live_path=repo /
  "DESIGN.md"`, and the module-docstring paragraph. Nothing removed. The
  no-row refusal message now names both sources and still names the sid
  ("extracted nor live DESIGN.md").
- `DESIGN.md` — workspace copy with the s59 section appended to section
  16 (ships cell kept check-compatible: no colon tokens, one file claim
  that exists in any extracted tree).

repo `src/`, `tests/`, and the live ledger: untouched (zero writes).

## Verified — ✅ real, run in scratch/repo (clone @ 2dd1b7f + checker commit), against real history

| check | case | result | evidence |
|---|---|---|---|
| fallback fires | s57 with the row removed from the extracted commit and present only in the live worktree (uncommitted) | rc=0, VERIFIED, pins 4/4 green in the extracted tree, record carries "ships row read from the live worktree (the close's own entry postdates the commit)" | outB2/log+rc, outB2/2026-09-16_check-s57.md |
| both present | s57 @ 1737437 honest close, live tree also has the row | rc=0, VERIFIED, disclosure absent (grep count 0) — extracted row wins | outA2/log+rc, outA2/2026-09-16_check-s57.md |
| fallback + tamper | s58 with the fresh row live-only AND src/rumpun/epics.py removed from the commit | rc=1, DELTA, "missing file: src/rumpun/epics.py" — the fallback never loosens binding | outC/log+rc, outC/2026-09-16_check-s58.md |
| seal tamper | s58 harvest body edited and committed | rc=1, DELTA (seal mismatch) | outD/log+rc, outD/2026-09-16_check-s58.md |
| unknown sid | s999, neither source has a row | rc=2, stderr names s999 and "extracted nor live DESIGN.md", no record written | outE/log+rc |
| pre-existing control | ORIGINAL checker on the s58 close commit | rc=1, DELTA "missing file: .rumpun/epics.yaml" — identical to my copy, so that delta predates this change | outORIG/log+rc, outORIG record |
| pins graft | s55+s56+s57 pin files run against the modified checker in the clone | 14 passed | pins-graft.log, pins-graft.rc (0) |
| lint + compile | ruff --no-respect-gitignore; py_compile | All checks passed; compiles | diff/ruff/compile in agent.log |

The s58 close case itself (both rows present) measures DELTA on the
pre-existing `.rumpun/epics.yaml` claim (see control row); the s58
fallback mechanics are the same code path proven by the s57 cases.

## Suite floor — ✅ measured in the clone (my checker is the only delta vs repo HEAD)

Full suite, clone working tree with the modified checker:
`260 passed, 2 skipped in 106.27s`, pytest exit 0, zero failures.
The two race-flake pins passed this run (load-dependent known flakes);
nothing else moved. Log: /tmp/s59w1-suite.log, copy in scratch/evidence.

## Residuals disclosed (report, not fixed — outside this season's scope)

1. Pins-at-close ordering: the fallback covers the row only. At a live
   close the extracted tree still lacks the season's own merged pins
   (they commit at close, after harvest), so the close check can refuse
   exit 2 at the pins step. Close order (commit the merge before
   harvest) or a pins-side fallback is the next scoping decision.
2. The s58 ships row claims `.rumpun/epics.yaml`; the file was never
   committed and does not exist in the repo, so `rumpun check s58
   <close>` DELTAs on it forever, original checker included. Operator
   follow-up: commit the epics declaration or amend the row at a future
   close; not silently patched here.

## Constraints held

- Ledger: zero writes (every checker run redirected --out-dir into the
  workspace scratch).
- tests/: untouched (w2 owns the pins).
- Workspace rule: all writes under .rumpun/runs/s59/w1/ (tools/ copy,
  DESIGN.md copy, notes.md, scratch/, evidence).
- logging, never print (the checker had no print; none added); ruff
  clean at line-length 100; py3.10+; stdlib only.
