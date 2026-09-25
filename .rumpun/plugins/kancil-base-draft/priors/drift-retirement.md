# A moved assumption re-seals; it is never silently dropped

## The prior

A sealed repro pins assumptions about current behavior. When the main
line moves and the repro's assumptions no longer hold, the corpus matrix
marks the repro as drift. Retirement is by re-seal: update the repro or
re-seal it against current behavior, with evidence. Removal without a
re-seal is not retirement; the mark stays a live candidate until a
re-seal lands.

## Why this holds

The same drift candidate recurred across successive reflection passes;
the recurrence was the signal, not noise. The retirement season's win was
the re-seal: the repro passes on current behavior with the moved
assumption updated, and the matrix runs green.

The end state to copy: reflection reads a fresh matrix every pass, a
FAIL/DRIFT row arms a candidate first, all-green prints a plain finding,
and an absent matrix changes nothing byte-for-byte.

## How to apply

- Refresh the matrix before reflection reads it; a stale matrix is a
  stale mirror.
- A drift mark carries: the repro, what moved, the observed behavior, and
  the WIN band (updated or re-sealed).
- The same candidate recurring across passes is the signal; repair the
  underlying assumption, never the signal.
