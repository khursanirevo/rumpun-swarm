# Ratified behavior stays under a replay gate

## The pattern

Behaviors ratified in the record become replay scripts run against the
current tree on demand and before reflection reads it. The gate
classifies honestly: pass, skip with a recorded reason, fail, drift. A
fail or drift row arms a candidate citing the script and the first
failing line; all-green prints a plain finding; a missing matrix changes
nothing.

## Why this holds

Judgments about current behavior rot: an assumption sealed in an old
repro moves when the main line moves, and a stale matrix then lies to
every reader. The gate makes the rot visible: the drift row names the
repro whose assumptions moved, and retirement is by re-seal against
current behavior with evidence.

## How to apply

- Every behavior worth citing later is worth a replay script; ratify it
  by landing the script, not a paragraph.
- Read a fresh matrix, never a stale one; refresh before reflection.
- A moved assumption is repaired by re-seal with evidence, never by
  removing the script.
