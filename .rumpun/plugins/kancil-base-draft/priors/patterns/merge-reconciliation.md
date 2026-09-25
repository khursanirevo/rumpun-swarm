# Reconcile divergent contracts at merge, by evidence

## The pattern

Units built in parallel from one spec land artifacts whose contracts
disagree: a name, an ordering, a default, a status code. Reconciliation
compares both artifacts against the spec, picks the stronger reading by
evidence, applies the delta as targeted edits, and records what moved
where the verdict can cite it.

## Why this holds

Left alone, a contract mismatch surfaces as red pins at integration and
costs a cycle. Named early and reconciled by evidence, it costs one edit.
The candidate readings are not equal: one usually satisfies more of the
recorded clauses, and that one wins.

## How to apply

- Compare both artifacts against the spec, not against each other alone.
- The stronger contract wins; the weaker artifact is edited to it, and
  the delta is recorded.
- Never reconcile by silently dropping one side's clauses.
