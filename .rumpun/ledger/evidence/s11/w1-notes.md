# s11 w1 — `src/rumpun/audit.py` + `rumpun audit` verb

Deliverables in this workspace only; nothing outside it touched.

| file | what it is |
|---|---|
| audit.py | new module `rumpun.audit`: `run_audit(root, last_n=10) -> Path`, `AuditError`, `candidate_lines(record)` |
| cli.py | repo cli.py at 93fddc0 + audit verb (diff is exactly: docstring v0.10.0, `audit as audit_mod` import, `cmd_audit`, the `audit [--last N]` subparser, `audit_mod.AuditError` in main's except tuple) |
| lane_tool.py | s9 precedent, posts/reads build-lane events via RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK |
| notes.md | this file |

## Trigger rules implemented (exhaustive — nothing else proposes a mutation)

- **Phase liveness (F1)**: declared phases from the LATEST musim yaml's
  `methodology.pipeline` (`phase`+`writes` pairs; entries missing either are
  skipped with a warning). Liveness K = engine seasons (window seasons whose
  `rimba/<sid>/` dir exists) holding `writes` on disk. Line template is the
  spec's literal: `phase P (writes W) wrote its artifact in K of N engine
  seasons (cited ids)`.
- **Stall recurrence (F2)**: count window seasons whose
  `rimba/<sid>/_season/state.json` status is `stopped_stall`; recurrence is
  flagged only at count >= 2. Seasons without state.json count in neither
  term.
- **Verdict histogram (F3)**: `verdict` values from every window season's
  `verdicts.jsonl`, keys WIN/LOSS/INVALID; other values surface as
  `other N`, never as a trigger. Rows without a `verdict` field do not
  count (defined rule, not a silent drop).
- **Candidates (max 3, deterministic order)**:
  1. phase trigger, pipeline order: liveness 0 across >= 2 engine seasons
     -> `exercise or trim phase P`, band: WIN when a later season's ledger
     holds the artifact or the pipeline drops the phase;
  2. stall trigger last: count >= 2 -> `re-size stall/budget rules`, band:
     WIN when a later season terminates without stopped_stall.
  Over-cap triggers are named in a `candidate cap 3 ... also unexercised
  but unproposed here` line — dropped, never silently.
- **Record**: id `audit-{k}`, k = 1 + count of `*_audit-N.md` filenames in
  akar/ (filename scan per spec, NOT declared-id scan — so a non-audit
  file declaring `id: audit-1` keeps k at 1 and the duplicate surfaces as
  `AuditError`); title `reflection audit`; body = findings + candidates,
  every line citing season ids. `akar.AkarError` wraps into `AuditError`;
  a corrupt state.json/verdicts.jsonl refuses the audit naming file+line.

## Deliberately left out (no evidence bar met, or out of scope)

- **Single-season stall**: count 1 (s4 today) is a finding, not a
  candidate — recurrence needs >= 2, else s11 would propose rule changes
  off one event.
- **Verdict-mix triggers** (LOSS/INVALID rate): no ratified deterministic
  rule; inventing one is policy pressure without a spec'd bar.
- **Partial liveness** (K >= 1 but < N): the phase demonstrably runs;
  trimming it would be evidence-free. Findings record it, no candidate.
- **Window seasons without a rimba dir**: contribute no artifact evidence
  (spec scopes artifact collection to rimba-present seasons); they appear
  only in the scope line and as `latest season` when newest.
- **Phase triggers beyond the cap**: today plan/falsify are #4/#5; they
  surface in the cap line only.
- **Citation-graph / hash-chain integrity checks** (P11/P28), artifact
  content schemas, mtime freshness: reflection over existence and engine
  state only in s11.

## Interpretation calls (flagging at integration)

- N in "K of N" = engine seasons (rimba dir present) in the window — the
  spec's "engine seasons" wording. w2's note read N as musim-window count;
  their 10 tests pass against this module as written (checked: the one
  fixture that could distinguish passes via the declared-phases line), so
  no red test either way. Recording the reading here.
- F1 carries the spec's literal template `wrote its artifact in K of N`
  (w2's pin caught my first wording `wrote W in K of N`; fixed).
- s11 itself is in-window (running, no artifacts): counts toward N and
  appears as `none in: s11` in F3 — a live season is honestly incomplete,
  not excluded.

## Integration notes

- `pyproject.toml` + `__init__.py` still say 0.9.0 (outside workspace);
  bump both to 0.10.0 at merge or the cli docstring note overstates.
- First integration run appends `audit-1` (akar/ holds zero audit-* files
  today). Expected first record over the real ledger: window s3..s12,
  engine seasons s3..s11 (9), execute/evaluate at 8 of 9 (s11 running),
  analyze/rank_gaps/hypothesize/plan/falsify at 0 of 9, stall count 1
  (s4), histogram WIN 18 / LOSS 4 / INVALID 5 over s3..s10, candidates
  analyze, rank_gaps, hypothesize (cap; plan, falsify named in cap line).

## Verification (✅ verified real; overlay = /tmp copy of repo + these files)

- `ruff check` clean: audit.py, cli.py, lane_tool.py (repo config,
  line-length 100, py310).
- Repo suite on overlay: **31 passed** (no test edits).
- w2's spec-first file against this module: **41 passed** (10 audit tests
  green pre-integration; their duplicate-id wrap, never-modifies, last_n
  window, stall and liveness triggers all exercised).
- e2e on a /tmp copy of the real .rumpun: exit 0, record + 3 candidates +
  cap line as predicted above; second run -> audit-2, first survives.
- Isolated stall-recurrence fixture: `re-size stall/budget rules` fires
  exactly once, citing both stalled sids.
- Corrupt verdicts.jsonl line -> exit 1, `ERROR <file>: line N is not
  valid JSON`, no traceback; `--last 0` and no-rimba projects -> exit 1.
- cli.py diff vs repo file = exactly the five intended additions.
