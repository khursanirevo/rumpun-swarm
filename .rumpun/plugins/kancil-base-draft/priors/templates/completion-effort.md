# The completion-effort contract

## What it is

The standing answer to the residual: repeated harness repairs make
autonomous delivery unproven, and completion effort outside the
stopped seasons is unquantified. The loop cannot certify autonomy
from inside. It can define what counts, and measure honest slices
toward it. This prior is that contract. It names its residual:
issue #16, the completion-effort contract. It stays open the same
way the sibling priors do (repro-backed-closure.md,
verdict-vs-correctness.md, baseline-comparison.md).

Three quantities:

1. Repairs-per-season. A correction commit is a commit whose subject
   starts with `fix:` or `chore:`. Each correction attributes to the
   season named in its subject; corrections with no season tag are
   campaign-level rows. The `chore:` subclasses stay separable:
   bookkeeping (check records, resume state), failure records, and
   repairs recorded as chores are not the same event, and pooling
   them inflates the repair count.
2. Recurrence. A repair class is the mechanism the subject names
   (the ships row, the pin path resolution, the checker surface
   resolution). A recurrence is a second repair in a known class
   after the class's first repair. Within-season arc iterations and
   across-closes re-fires are different shapes; the record states
   which it counted.
3. The operator-effort counterfactual. The repairs the operator
   never made. The version control system cannot certify this by
   itself: the harness commits under the operator's identity, so
   operator and harness activity are confounded at the source. The
   slice reports the confound, corroborates with the campaign trail
   (ledger check records, the board trail), and labels the
   operator's non-involvement as trail claim plus operator
   assertion, never as a git-measured zero.

## The skeleton

    # one row per season touched:
    | season | fix: | chore: | chore subclass | classes fired |
    # one row per repair class, recurrences beyond the class's first fire:
    | class | fires | re-fires | first to last season |
    # the caption carries the honesty line, verbatim:
    "A single-side table over one campaign is a first data point. It
    proves nothing alone."

The forward item the contract puts on the loop: give the harness its
own committer identity (a distinct committer field or a bot
account). Until then the operator column is confounded, not zero.

## How to apply

- Source: the git log over the campaign window. Correction =
  subject prefix `fix:`/`chore:`. Attribution = the season id in the
  subject. Report the prefix totals, the touched-season count, and
  the corrections-per-close ratio with its denominator stated.
- Recurrence: class = the mechanism named in the subject. Count
  re-fires beyond each class's first repair; state the window; split
  within-arc iterations from across-closes re-fires.
- Operator side: state the identity confound in every table that
  carries an operator column. Corroborate with the trail. Label the
  assertion. A distinct harness identity makes the column
  measurable; land it before the next campaign if the column
  matters.
- Closing rule: the residual issue stays open until the
  counterfactual becomes measurable (a distinct identity or a manual
  dataset) or the operator ratifies the trail as the counterfactual.
  No season closes it; a season that measures a slice cites the
  standard, not a resolution.
