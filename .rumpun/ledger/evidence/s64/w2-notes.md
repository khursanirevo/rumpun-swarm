# s64 w2 notes — spec-first pins for the count honesty

## Spec anchors

- w1 brief: .rumpun/runs/s64/w1/prompt.md (the counts read the whole
  ledger; the salvaged split propagates wherever totals render).
- Ledger records: usefulness-decade-5 (residual: "Salvaged stopped
  seasons earn WIN alongside completed seasons. Aggregate verdicts
  obscure execution reliability and intervention costs.") and audit-41
  (F3 histogram, 60 yamls at the time, decade-5 due).
- Precedent shape: .rumpun/runs/s63/w2/tests/test_s63_w2_pins.py.
- s62 mark format: `"salvaged": true` on the verdict row; agreed split
  shape "X WIN (Y salvaged)" (s62 harvest observed).

## The pins (tests/test_s64_w2_pins.py, additions-only)

1. `test_s64w2_slot_counts_sum_to_the_season_total` — fixture ledger of
   6 seasons (4 verdict rows: WIN/LOSS/NEUTRAL/INVALID, 1 running with
   state.json status "running", 1 missing) yields 4 classified + 1
   running + 1 missing; the six slots sum to the total 6; the composed
   brief names the counts (each verdict 1, running 1, missing 1, total
   6). Nothing blurs into run/drafted-only.
2. `test_s64w2_salvaged_split_reads_through` — fixture with one
   `"salvaged": true` WIN shows the split in the counts: win 2, of
   which salvaged 1, loss 1, missing 1, sum 4.
3. `test_s64w2_real_ledger_counts_captured_for_notes` — the composer's
   slot surface over the real campaign ledger, read-only; the counts
   are captured for these notes and only the structural shape is
   asserted. The fixture pins carry all value assertions.

Every pin runs a bounded subprocess driver (timeout 240s) that imports
tools/usefulness_audit.py by path and calls its surfaces read-only.
Why not the composer CLI: the decade gate refuses before composing when
the ledger owes no decade (floor(count/10) == 0 for the 6-season
fixture), so a spec-sized fixture cannot reach compose_brief through
run(). The driver binds the counting surface by candidate name
(season_slots, season_counts, ledger_counts, count_season_slots,
season_split) and auto-fills compose_brief's counts param with the
counter's own result.

## Measured red set (season start, git da2f444)

✅ measured — /tmp/s64w2-pytest-run1.log: 3 failed in 0.56s.

| pin | failure (right spec reason) |
|---|---|
| 1 | no classified slots on `season_split` (raw `(5, 1)`) |
| 2 | no classified slots on `season_split` (raw `(3, 1)`) |
| 3 | no classified slots on `season_split` (raw `(63, 1)`, real ledger) |

The blur is visible in the raw tuples: the 4 classified plus the
missing season collapse into "drafted-only", and the salvaged mark has
no surface at all.

Mid-landing sequence, honestly: w1 landed the composer change while
these pins were being measured. run3 failed on a driver defect, not a
spec reason — importlib loading without `sys.modules` registration
breaks dataclass processing on py3.12+ (KW_ONLY resolution); fixed in
the driver. Runs 4-5 bind the landed `ledger_counts`/`LedgerCounts`
surface: 3 passed (run4 0.63s, run5 0.33s). Surface bindings that
reconciled to the landed shapes: candidate list hit `ledger_counts`;
compose_brief's required `counts` param auto-filled; history rows
reconciled to the landed `(sid, verdict, salvaged)` triples.

## Green at merge (against the landed tools/ change)

✅ measured — /tmp/s64w2-pytest-run5.log: 3 passed in 0.33s;
py_compile OK; `~/.local/bin/ruff check --no-respect-gitignore` clean
(line-length 100). The tools/ change is uncommitted in the worktree
(`M tools/usefulness_audit.py`, mtime 18:39:44); if its shape moves
again, the driver's binding assumptions in the pins docstring are the
reconciliation surface.

## Real-ledger counts (reported, not asserted)

✅ measured — driver run over .rumpun (/tmp/s64w2_real_counts.json):

```
surface: ledger_counts
slots: WIN 52, LOSS 9, NEUTRAL 0, INVALID 0, MISSING 2 (s1, s43)
salvaged: all 0 (no "salvaged": true rows on the live ledger yet)
running: s64
```

The arithmetic holds: 52+9+0+0+2 slots + 1 running = 64, the number of
season yamls matching ^s<N>.yaml$ (the seasons dir also holds
_template.yaml). s43 missing matches decade-5's residual about DESIGN
labeling s43 WIN with no verdict row on the ledger.

## Suite floor

✅ measured — full suite over the landed tree,
/tmp/s64w2-suite.log: 1 failed, 278 passed in 226.73s. The one failure
is `test_s38_coldstart_checker_leaves_repo_rumpun_untouched`, and its
diff is exactly the live worker files of this workspace
(.rumpun/runs/s64/w2/agent.log, state.json) changing during the run —
the documented live-season red for the coldstart snapshot pin, not a
regression from these additions (the pins run in pytest tmp_path and
write nothing under the repo). My 3 pins are inside the 278 passed.
