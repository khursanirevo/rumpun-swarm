# s63 w1 — the ships classifier learns runtime artifacts

Status: done and verified. The clause judge in tools/artifact_check.py now
classifies file-shaped tokens (runtime-framed vs committed-tree claim),
binds runtime-framed tokens to the live runs state, and names the
classification in the clause evidence. Ghost committed claims still DELTA.

## What changed (tools/artifact_check.py, additive)

- `FileClaim` dataclass + `ShipClause.file_claims` — one record per
  file-shaped token: kind ("committed" | "runtime" |
  "runtime-committed-fallback"), present, where.
- `runtime_framed()` — three framing signals: "writes <token>",
  a runs/&lt;sid&gt;/ path prefix, a close-time cue ("at close", "close-time",
  "on close") in the token's top-level comma/semicolon segment
  (`_segment_bounds` is paren-aware, matching `split_clauses`).
- `resolve_runtime()` — binds against the live runs state
  (`--repo`/.rumpun/runs/&lt;sid&gt;/): runs/&lt;sid&gt;/-prefixed or path-shaped tokens
  resolve below the dir; a bare token binds at the runs root only, never by
  deep basename match (scratch debris under w1/scratch can never launder a
  claim — checked against the real s61 state, whose only results.jsonl
  copies are scratch copies).
- `analyze_clause(..., sid="", runs_dir=None)` — the classification runs
  only when runs_dir is bound; None keeps every token committed-bound, the
  exact pre-s63 behavior (old 3-arg callers unchanged).
- Committed-tree fallback: a runtime-framed token the runs state lacks but
  the extracted tree carries binds committed, and the evidence names the
  fallback ("absent from runs/&lt;sid&gt;/, bound committed"). Found via the
  floor probe: the s54 honest-close pins broke because "the direct verb
  reads and writes .rumpun/ledger/directives.jsonl" is genuinely carried by
  the s54 tree. Absent from both surfaces still DELTAs, so the framing is
  never a bailout.
- Rendering names the classification per token; the module docstring's
  SHIPS section and DELTA line document it.

## Verification (✅ verified real, measured this session)

- Fixture harness `fixture_close.py` (this workspace), five cases over a
  miniature campaign repo (one close commit, live runs state uncommitted):
  - fxw "writes results.jsonl at close" with runs/fxw/results.jsonl present
    → exit 0 VERIFIED; evidence: "runtime artifact results.jsonl PRESENT
    (runs/fxw/results.jsonl) (runtime-checked against runs/fxw/)".
  - fxc ghost_report.md, no runtime framing → exit 1 DELTA, "missing file:
    ghost_report.md", evidence names "committed-tree claim" for the ghost,
    the two present files, and engine.py.
  - fxr runtime framing, runs state absent → exit 1 DELTA "missing runtime
    artifact ... runs state ... absent" (no bailout).
  - fxb "writes ledger.jsonl", runs state absent, tree carries it → exit 0
    VERIFIED via the named committed fallback.
  - s61 recheck (real close ca333a3, --out-dir inside the workspace):
    results.jsonl classifies runtime-framed ("runtime-checked against
    runs/s61/"); verdict DELTA — the live s61 runs state genuinely holds no
    root results.jsonl (only scratch copies under w1/scratch; `find`
    checked), so the delta is honest with the corrected reason "missing
    runtime artifact" instead of the old wrong "missing file". The s61
    false-positive mechanism is fixed; the artifact itself is absent from
    the s61 runs state.
- Floor: the four checker pin files (s55/s56/s57/s59 w2 pins, which run
  this tool as a subprocess) — 18 passed, 0 failed after the fallback fix;
  the pre-fix run measured 2 failed (both s54 honest-close pins), which is
  what surfaced the fallback requirement.
- ruff (`~/.local/bin/ruff --no-respect-gitignore`, line-length 100):
  clean on tools/artifact_check.py and fixture_close.py. py_compile clean.
  logging only; stdlib only; py3.10+ (`from __future__ import annotations`
  already present). tests/ untouched (w2 owns the pins).

## Artifacts

- tools/artifact_check.py — the documented minimal change (four code
  regions + docstring).
- fixture_close.py — the five-case verification harness (rerunnable;
  rebuilds its fixture and out dirs from scratch each run).
- out/a..d, out/s61recheck, out/s54probe — the check records this session
  produced, kept as evidence.

## For the harness merge

- No tests/ changes; w2's pins should target runtime_framed, resolve_runtime,
  FileClaim, and the fallback path if they want unit-level pins.
- No ledger writes; every record landed in workspace out-dirs.
