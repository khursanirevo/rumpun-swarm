# Pin the contract red, then make it green

## The pattern

Before implementing a change, write the pins that state its contract, run
them against the unpatched tree, and record the red set. The measured red
run is the evidence the pins test the coming change and not existing
behavior. At integration the same pins run green; a suite that was never
red pins nothing.

## Why this holds

Pins written after the code pass on it by construction; they describe what
is, not what was promised. A recorded red set makes the pins falsifiable:
it names what fails before the fix, so a later green run carries weight,
and a pin that cannot fail is honest about testing nothing.

## How to apply

- Name the interface in the pins before any implementation exists; the
  declaration is the reference both sides reconcile against at merge.
- Run the pins against the unpatched tree and record the red set with
  reasons.
- At integration the same pins run green; a still-red pin blocks and is
  reported, never skipped.
