# The verdict-vs-correctness line

## What it is

The standing epistemic standard behind issue #5's repro-backed closure
contract: a recorded verdict establishes what an evaluator wrote
against the season's declared band. It does not establish
implementation correctness, and it does not establish practical value.
The repro-backed closure contract (repro-backed-closure.md, the
sibling prior) answers the filed-defect shape: a season that resolves
a filed defect closes only against the issue's own repro, red before
the fix and green after. This prior draws the line the contract sits
inside, for every other claim a season makes:

- What a verdict establishes: the evaluator's judgment against the
  declared band, as recorded. Nothing else.
- What only a repro establishes: implementation correctness for a
  filed defect. A band verdict is not a repro; the sibling contract
  governs that shape.
- What only an external task or a matched baseline establishes:
  practical value — that the loop's output does a real job or beats a
  fixed workflow. No verdict establishes this. The decade reviews name
  it a residual every time; it stays a residual until the campaign
  runs the external task or the matched baseline.

## The skeleton

    # the claim words map to evidence classes; the harvest states the class:
    verdict: WIN          -> establishes: what the evaluator wrote against the band
    implies: ... repro ... -> establishes: implementation correctness (sibling contract)
    implies: ... external task ... baseline ... -> establishes: practical value
    no repro, no external task, no baseline -> the harvest states the claim's class
                                                and its absence, by name

## How to apply

- Cite a verdict as what it is: what the evaluator wrote against the
  band. The words "correct" and "works" do not follow from a verdict
  line; a season that needs them cites a repro.
- A season claiming correctness for a filed defect follows the
  sibling contract: the repro-backed closure
  (priors/templates/repro-backed-closure.md), red-before/green-after,
  cited by pin name.
- A season claiming practical value names the external task or the
  matched baseline it ran; absent both, the harvest's implies states
  the claim is unestablished. Stated absence beats silent absence.
- Issue #5 carries this line as the standing standard, deliberately
  open next to the repro-backed closure contract. No season closes
  it; a season that applies it cites the standard, not a resolution.
