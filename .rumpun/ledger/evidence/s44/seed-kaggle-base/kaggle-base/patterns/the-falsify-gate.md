# The falsify gate

A cycle that claims a verdict owes itself disconfirming evidence.

Rule: a cycle declaring its conclusion falsifiable must give at least one
step the job of reading an artifact the cycle's own execution produced.
A verdict facing nothing it could read and reject is a words-only
invariant: the declaration exists, the disconfirmation cannot.

In practice:

- Give the reading step the artifact another step writes.
- The lean two-phase shape satisfies the gate: one phase executes and
  writes the results artifact; a later phase reads those results and
  writes the verdict.
- A reader of a file nothing in the plan produces does not count. An
  external input cannot disconfirm the cycle's own claim.

The gate errors at lint time, naming the cycle and the unreachable
artifact.

Generalized from: the falsify-gate pattern of a prior verification
campaign — a lint rule that turned a declared falsifiability invariant
into enforced truth by demanding a reachable disconfirming input.
