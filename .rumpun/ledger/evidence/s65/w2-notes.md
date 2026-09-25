# s65 w2 notes — spec-first pins for the containment gate

## Spec anchors

- w1 brief: .rumpun/runs/s65/w1/prompt.md (the gate reads the previous
  close's check record; DELTA or refusal blocks with the record named;
  a VERIFIED rerun or waiver releases).
- Ledger records: s64-harvest, check-s63 (the DELTA record that stood
  unresolved), usefulness-decade-5 (residual: "Artifact-check refusal
  or DELTA leaves WIN intact. The brief does not establish mandatory
  containment before subsequent work.").
- Precedent shape: tests/test_s60_w2_pins.py (the season-start
  subprocess pattern) and test_s64_w2_pins.py (docstring/notes
  contract).

## The pins (tests/test_s65_w2_pins.py, additions-only)

1. `test_s65w2_delta_check_blocks_the_next_start` — the fixture
   campaign closes s650 through the real engine (stub route `true`:
   no quota, no network), writes one DELTA check-s650 record dated
   after the close, starts s651. Must refuse nonzero and name
   check-s650. A lint pre-assert isolates fixture validity (a lint
   refusal exits nonzero without naming the record).
2. `test_s65w2_verified_and_waiver_release_the_block` — arm a: DELTA
   then a later VERIFIED rerun record check-s650-2, start succeeds and
   persists completed. Arm b: DELTA stands, the operator appends
   waiver-s650 through the landed `rumpun waive` verb (--reason names
   the check), start succeeds and persists completed.
3. `test_s65w2_clean_campaigns_start_normally` — arm a: previous
   season closed completed, zero check records, s651 starts. Arm b:
   fresh campaign, nothing closed, the first season starts.

Every pin runs the real CLI as a bounded subprocess (240s cap, the
task bound; the 0.1-minute stall rule bounds any wedged season inside
the engine). Fixture campaigns live wholly under pytest tmp_path; no
pin touches the repo, the ledger, or a live season.

## Measured sequence (2026-09-16; logs /tmp/s65w2-pytest-run*.log)

Mid-landing, honestly: w1's gate landed in the worktree during pin
authoring (engine.py containment_block/check_block/has_waiver/
_prev_closed_season/newest_check_record + cli.py cmd_waive, uncommitted
at measurement time), so the first measurement already ran against it.

✅ measured — run1 (pytest rc 1): pins 1 and 3 passed against the
landed gate; pin 2 failed on a fixture-shape mismatch, not a spec
reason: my rerun was a re-dated same-id record (2026-09-16_check-
s650.md, VERIFIED); the landed gate resolves the id check-s650 to the
DELTA and correctly kept the block. The landed rerun convention (a
rerun appends under the suffixed id check-<sid>-<rerun>; the akar
discipline refuses a duplicate id) is coherent — the checker itself
refuses an existing check-<sid> file, so a re-dated same-id record
cannot even be appended through the discipline.

✅ measured — run2 and run3 after reconciling the fixtures to the
landed shapes: 3 passed (run2 5.57s, run3 7.35s); ruff clean
(`~/.local/bin/ruff check --no-respect-gitignore`, line-length 100);
py_compile clean.

⚠️ not measured: the pre-landing red (pin 1 against a gateless tree).
w1 landed before any measurement, so pin 1's green rests entirely on
the landed gate. ⚠️ expected-projected only: without the gate, start
exits 0 past the standing DELTA (the decade-5 gap verbatim).

## Merge-time items (not claimable from here)

- Green at merge: run3 measured the current worktree (w1's src/ edits
  uncommitted, mtime in-flight). The harness re-checks at merge; the
  fixture-shape bindings above are the reconciliation surface.
- Suite floor: deliberately not run here. The full suite races this
  season's live workers over src/ and the s38 coldstart pin reads the
  live .rumpun tree; the floor is certified at merge per the
  shared-lane rule (py_compile probe green here).

## Fixture-shape bindings (if w1's shapes move again)

- Check records: id check-<sid> or check-<sid>-<rerun>, date-stamped
  filename, season + verdict body lines (engine.newest_check_record,
  _record_verdict; newest = max by (filename date prefix, id)).
- Waiver: id waiver-<sid> or waiver:<sid> (engine.has_waiver),
  appended by `rumpun waive <sid> --reason ...` (cli.cmd_waive).
- Previous closed season: newest closed season below sid in sN order,
  terminal persisted status (engine._prev_closed_season).
- Block surface: engine.start_season raises EngineError before any
  state write, lock, or spawn; main() logs it and exits 1; the message
  names the record and both release paths.
