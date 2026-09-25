# The evidence record

## What it is

One append-only record per event worth citing later: a header naming the
record kind, identity and date, the scope it covered, findings as plain
lines, and a content digest sealing the bytes. Records are never edited
after the seal; a correction lands as a new record citing the old one.

## The skeleton

    # evidence record: <kind>
    id: <kind><number>
    date: <YYYY-MM-DD>
    title: <one line>
    scope: <what the reflection covered>
    finding: <one plain line per finding, counts included>
    sha256: <digest of the record's bytes>

## How to apply

- The digest seals the record's own bytes, appended last; the seal is
  the tamper evidence.
- Findings state the facts with counts; candidates arm from findings by
  rule, not by prose.
- Citations name the record id plus a digest prefix; the id is stable
  forever.
