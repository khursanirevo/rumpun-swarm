# s95 w1 — the spend line lands; the label split renders live

The s94 cost contract named the forward fix: a per-harvest spend line
derived from the writer table. Land it, and catch the label split
rendering live.

## Ground truth (measured 2026-09-18)
- the s94 contract: priors/templates/cost-accounting.md (the
  spend-line skeleton: writer-seconds per season, the unrecordables
  named); issue #18 OPEN carrying it
- the composer (tools/usefulness_audit.py): the label split landed
  (the WIN cell reads "N WIN (I in-lane, P post-stop integration, of
  which M salvaged)"; plain ledgers byte-identical) — its test is in
  tests/test_s94_w1_pins.py; the LIVE render has never been seen
- every harvest record carries the per-writer table (route, seconds)

## Task
1. Land the spend line: the harvest verb (or the composer's harvest
   ingest) emits a spend line per season — total writer-seconds from
   the per-writer table, the shape per the cost-accounting template.
   Offline-pinnable (tests/test_s95_w1_pins.py, _s95w1_ prefix).
2. Run the composer fresh over the current ledger: the label split
   renders live (the 5 post-stop integration wins in the WIN cell),
   the spend lines appear, and plain ledgers stay byte-identical
   (the s94 pin's contract re-verified on live data). notes.md
   REQUIRED: the fresh render.
3. Verify: tests/test_s94_w1_pins.py + your pins solo; green.

## Bounds
- Edits: tools/usefulness_audit.py, tests/. notes.md REQUIRED. No
  live gh call.
