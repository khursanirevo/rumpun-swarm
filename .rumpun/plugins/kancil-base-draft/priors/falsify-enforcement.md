# Seal the kill test before the run

## The prior

Before any execution that could be reported as a success, seal a
falsification record: comparator, metric, threshold, dataset, confidence.
The seal happens before execution; a kill test written after the result is
not a seal.

## Why this holds

Vacuous kill tests ("the script runs", "the loss went down") are the
failure mode: they pass on anything, so they prove nothing. A record
sealed before the run cannot be shaped to flatter the result. The
strongest form is a detector that falsifies its own premise: it can come
back with the premise dead, and that still counts, because the sealed
record is what makes the negative outcome evidence.

## How to apply

- Every claimed improvement names, in advance, the test that would kill it.
- The record carries comparator, metric, threshold, dataset, confidence.
- Verdict classes: kill, revise, retain, inconclusive; every verdict names
  its consequence.
- An evaluator's written verdict is a claim, not independent proof; weight
  travels with independent artifact checks. A negative outcome with a
  sealed record outranks a positive outcome without one.
