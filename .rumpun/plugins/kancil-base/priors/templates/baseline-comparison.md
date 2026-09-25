# The baseline comparison

## What it is

The standing answer to the residual: no baseline comparison
establishes that the season loop improves delivery speed, quality, or
cost over ordinary development. The loop cannot prove its own value
from inside; it can design what would count, and measure honest
slices toward it. This prior is that design. It stays deliberately
open until paired data exists, the same standing shape as the
sibling priors (repro-backed-closure.md, verdict-vs-correctness.md).
It names its residual: issue #15, the baseline comparison.

A fair comparison pairs like-for-like on three metrics:

1. Time-to-fix a filed defect. The loop's side: board-pulled
   seasons, filed-to-closed on the board. The baseline side: the
   operator's manual turnaround on khursanirevo/exp_manager issues,
   same defect classes, filed the same way, the operator's own
   clock. No manual dataset exists on the loop's box yet; the
   loop-side column can fill first, and says so when it does.
2. Defect escape rate. A check record's DELTA row is a catch; an
   escape is a defect observed in a shipped artifact with no prior
   check record catching it. Rate = escapes / (catches + escapes),
   measured per audit window. The baseline side: the operator's
   hand-run reviewer and release workflow.
3. Repair recurrence rate. A fix recurs when its repro pin goes red
   after closure or the same defect shape re-files. Rate =
   recurrences / closed fixes, stated with its observation window.
   The baseline side: the operator's manual re-open and re-file
   rate over the same window.

## The skeleton

    # one row per defect; the clock and the window are stated, never implied:
    | defect | filed (first record) | closed (record) | elapsed | fixed through | recurrence window | recurrences |

    # the table's caption carries the honesty line, verbatim:
    "A one-sided table of five is a first data point. It proves
    nothing alone."

## How to apply

- The clock: the board's own timestamps (created_at, closed_at) are
  the primary clock. When a slice must run from the ledger alone,
  the commit clock is the declared proxy: the filing record's commit
  to the closure record's commit, and the table header says "commit
  clock".
- Pairing: compare the same defect classes, filed by the same actor,
  on the same clock. A loop-side sample without its baseline-side
  pair is a data point, not a verdict.
- Bands: a WIN or LOSS claim needs paired samples on both sides and
  a threshold decided before the table is read. Below that, the only
  honest verdict is "first slice, no comparison yet", and the slice
  still gets measured and posted, because a blank cannot accrue.
- Recurrence: every closure cites its pin (the repro-backed closure
  contract); a recurrence is a red repro pin or a same-shape re-file
  after closure. State the observation window next to the zero.
- The residual issue stays open until a paired comparison exists.
  No season closes it; a season that measures a slice cites the
  standard, not a resolution.
