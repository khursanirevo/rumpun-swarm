# Close every unit with a harvest record

## The pattern

A finished unit closes with a harvest record: the verdict, the outcome
line stating what the work implies for the next iteration, and pointers
to the salvage. A unit that stops without its record loses its salvage;
the next attempt starts from zero instead of the recorded state.

## Why this holds

The salvage loop proved itself repeatedly: drafts written but not landed
by a stopped unit were harvested, applied, gated, and landed by the next
attempt. Each rescue cost one cycle instead of a rebuild from scratch.
The record is what makes the salvage findable; without it the next
attempt cannot know the work exists.

## How to apply

- Write the record at close, win or loss; a loss still ships its
  implications and salvage pointers.
- The implies line is the successor's first input.
- A stopped unit's work is harvested and gated before the successor
  builds on it.
