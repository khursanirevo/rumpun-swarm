# s64 w1 — the counts read the whole ledger

Status: composer change landed and verified; suite floor run completing,
final numbers in the Suite floor section below.

## What changed (tools/usefulness_audit.py, additive, documented)

- `LedgerCounts` (frozen dataclass) + `ledger_counts(root)`: every
  seasons/s<N>.yaml lands in exactly one verdict slot — WIN, LOSS,
  NEUTRAL, INVALID from the last season-level verdicts row (report verb
  rule [H]), or MISSING (no such row and the season is not running; a
  season without a state.json is not provably running). `render()` emits
  the one-line summary the brief facts block carries.
- `verdict_history` returns (sid, verdict, salvaged) triples; the brief's
  history block marks a salvaged win "s<sid>: WIN (salvaged)". The two
  row readers are shared via `_last_season_row`; `_season_status` reads
  the persisted status. Both refuse on corrupt input.
- `compose_brief` takes the counts and renders the line after the
  "season yamls" facts line; `run()` computes and logs the counts
  ("whole-ledger counts: ...") before composing.
- Module docstring documents the s64 whole-ledger counts.

## Spec reading (the one gap, resolved and documented)

- The deliverable defines MISSING as "no verdict row and not running"
  and requires exactly one slot per yaml. s64 itself is running, so the
  running season is NAMED in the counts line ("; 1 running (s64)") and
  holds no slot: sum(slots) + len(running) == yaml total is the
  invariant, and nothing running is ever counted missing. The five
  slots still cover every non-running yaml.
- Salvage split: the WIN cell renders "X WIN, of which Y salvaged" only
  when the ledger holds at least one row marked "salvaged": true; with
  none marked the line stays plain (the s62 w2 agreed shape: the
  unmarked form is byte-identical to the plain cells). The split reads
  the s62 row marks as they stand; nothing rewritten.
- Denominator: the composer's own season_count (the s<N>.yaml pattern).
  The seasons dir holds 65 entries; the 65th is _template.yaml, not a
  season, so 64 is the honest ledger total.

## Verification (✅ verified real, measured this session)

- verify_counts.py (this workspace, rerunnable, rc 0):
  - Real ledger: "season verdict slots: 52 WIN, 9 LOSS, 0 NEUTRAL,
    0 INVALID, 2 MISSING (s1, s43); 1 running (s64)" — 63 season slots
    (60+ ✓), missing named ✓, slots + running == 64 ✓, counts line
    present in the composed brief (out/brief_preview.txt, real history
    including "s64: none").
  - The counts surface exactly what usefulness-decade-5 residual 9
    flagged: s43 has no season-level verdict row (DESIGN labels it WIN,
    the verdict ledger records none), and s1 predates the row
    mechanism. Both are now named MISSING.
  - Fixture: "season verdict slots: 2 WIN, of which 1 salvaged, 0 LOSS,
    0 NEUTRAL, 0 INVALID, 2 MISSING (s4, s5); 1 running (s3)"; history
    renders "s1: WIN (salvaged)" while the plain win stays unmarked.
  - Fail-closed refusals: corrupt verdicts line, unknown season-level
    verdict string, corrupt state.json — all UsefulnessAuditError.
  - One bug caught by the real-ledger assertion and fixed: the MISSING
    slot was never incremented (the line read "0 MISSING (s1, s43)"),
    which broke sum + running == total; fixed, rerun green.
- ruff (--no-respect-gitignore, line-length 100): clean on
  tools/usefulness_audit.py and verify_counts.py. py_compile clean.
  logging only; stdlib only; py3.10+.
- No ledger or src/ writes: verification reads the real ledger and
  writes only under this workspace (out/brief_preview.txt). No route
  call, no record appended.

## Suite floor

Full suite: 1 failed, 278 passed (209s, /tmp/s64w1_floor.log). The
single red is the documented in-suite s38 coldstart snapshot pin
(test_rumpun.py::test_s38_coldstart_checker_leaves_repo_rumpun_untouched):
it snapshots the repo .rumpun tree around a checker run and the live s64
worker files moved inside that window (w1/w2 agent.log, state.json,
verify_counts.py); the checker itself exited 0, 11/11 steps PASS. This
is the known live-season red (the s38 memory: expect it red in-suite,
prove via checker exit 0 plus worker-file deltas — both present). No red
from the composer change; nothing skipped.

## Artifacts

- tools/usefulness_audit.py — the documented tools/ change (docstring,
  two constants, `_season_status`, `_last_season_row`, `LedgerCounts`,
  `ledger_counts`, `_season_number`, `verdict_history` triples,
  `compose_brief`, `run` wiring).
- verify_counts.py — the verification harness (rerunnable; real-ledger
  part is read-only over the ledger, fixture part self-contained).
- out/brief_preview.txt — the real brief composed this session.

## For the harness merge

- No tests/ or src/ changes; w2 owns the pins. Pin surfaces:
  `ledger_counts` / `LedgerCounts.render` / `verdict_history` (importlib
  from tools/usefulness_audit.py) or a subprocess run asserting the
  facts line. The counts-line format contract lives in
  `LedgerCounts.render`.
- Known-good baseline: the composer's subprocess pins in test_rumpun.py
  run over fixture seasons whose verdict rows carry no season key, so
  every fixture season lands MISSING and no refusal fires.
