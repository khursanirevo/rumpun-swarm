# The harvest record

## What it is

The record a unit closes with. Fixed rows carry who ran, on what route,
in what state, with what exit code and duration; then the verdict, the
implies line, and the digest sealing the record's bytes.

## The skeleton

    # evidence record: <unit id>-harvest
    id: <unit id>-harvest
    date: <YYYY-MM-DD>
    title: <the unit's title>
    verdict: <win or loss, as graded against the sealed band>
    implies: <what the outcome implies for the next unit>
    sha256: <digest of the record's bytes>

## How to apply

- Write it at close, not later; a late record is a claim without a seal.
- The implies line is the successor's first input.
- Losses carry the same fields as wins; the digest seal is unconditional.
