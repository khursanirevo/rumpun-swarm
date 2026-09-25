# The cost-accounting contract

## What it is

The standing answer to the residual: the campaign supplies no total
cost accounting, and the last explicit cost-cap status remains unset
despite a declared budget invariant. The residual is about
visibility, not enforcement: directive seq 9 sets no cap
deliberately (usefulness exhaustion is the stopping criterion, not
money), so what the campaign spends is unrecorded. The loop cannot
reconstruct spend retroactively. It can define what counts as cost,
measure honest slices of it, and stop leaving the spend line out of
every close. This prior is that contract. It names its residual:
issue #18, the cost-accounting contract. It stays open the same way
the sibling priors do (repro-backed-closure.md,
verdict-vs-correctness.md, baseline-comparison.md,
completion-effort.md).

## What counts as cost, honestly

Measurable from the trail:

1. Writer-seconds per season. The harvest writer table records route
   and seconds per writer; the season line records the duration. The
   season's spend is the sum of the seconds column. Writers run in
   parallel, so writer-seconds exceeds wall-clock duration; the two
   are different units, and the record states which it reports.
2. Seasons per week. The ledger record dates count seasons closed
   per calendar day. Throughput is a cost line: it bounds what a
   slice of machine time buys, and it is the only spend axis the
   campaign already measures on every close.
3. The board defects' filed-to-closed elapsed times. Issue
   timestamps bound the repair latency the campaign imposes on
   itself; the slice reports a range with the open count, not an
   average to optimize.

Not measurable, retroactively or now:

- Token counts. No record in the trail carries them; no historical
  slice exists and none can be reconstructed.
- API cost. No billing surface writes to the trail; no price table
  applies honestly after the fact.
- The operator's manual-time counterweight. Unrecorded, so the
  autonomous-spend-versus-manual-effort comparison stays open until
  the operator records it.

## The skeleton

    # one row per harvested season:
    | season | writers | writer_seconds | duration_s |
    # the spend line, per harvest, derived from the writer table:
    spend: writers=<n> writer_seconds=<sum> duration_s=<season duration>
    # the caption carries the honesty line, verbatim:
    "The table proves nothing alone: seconds are not money, and the
    unrecorded columns (tokens, API cost, operator time) stay
    invisible."

## The visibility fix going forward

Every harvest close derives and records the spend line from the
writer table it already holds. No new collection: the line is a
derived view of data the record already carries. A future
provider-side counter (tokens, API cost) extends the line; it never
rewrites history.

## How to apply

- Source: the ledger's *-harvest.md records. Sum the writer table's
  seconds column per season; state the season count and any excluded
  record that predates the writer table next to the total.
- State the cap status with every slice: campaign_cost_cap is unset
  by directive seq 9, deliberately; the budget invariant is a hard
  invariant the panel cannot waive. Unset is not unmanaged: per-
  writer budgets and the stall rule bound each season; the first
  budget stop proves it fires.
- Report elapsed board times as a range (first to last) plus the
  count of still-open issues; a range over one campaign is context,
  not a benchmark.
- State the unit: writer-seconds are machine-seconds billed to
  writers, not money and not wall-clock.

## Closing rule

The residual issue stays open until a spend line lands in the
harvest schema (then the slice becomes a routine derived view) or
the operator records the manual-time counterweight. No season closes
it; a season that measures a slice cites the standard, not a
resolution.
