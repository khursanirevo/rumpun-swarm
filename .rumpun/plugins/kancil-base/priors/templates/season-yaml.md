# The season declaration

## What it is

One file declares a unit of work: identity and parent, goal, the metric
it is judged by, the declared change with its evidence citations, and
the expected band written before the run. The band states the clauses
that make the outcome a win; the clauses are each checkable after the
run, and anything unmet is recorded honestly.

## The skeleton

    id: <unit id>
    parent: <the unit this one builds on, or none for a seed>
    goal: <one sentence, plain>
    metric: <the measure this unit is judged by>
    methodology:
      evidence:
        - <record kind>:<record id>@<content digest>
      primary_change:
        type: <add, remove, rewire, retune>
        baseline: <what stood before, and how it shows in the metric>
        expected_band: "WIN if <clauses, each checkable after the run>"

## How to apply

- Write the band before the run; grading against a band invented after
  the run proves nothing.
- Every evidence citation names the record and the digest that seals it.
- The declaration is the unit's contract; views render from it, never
  the reverse.
