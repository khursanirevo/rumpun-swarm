# The repro-backed closure

## What it is

The standing standard for the epistemics gap: recorded verdicts
establish what evaluators wrote; they do not establish implementation
correctness. A season that resolves a filed defect closes only against
the issue's own repro: the repro rebuilt from the issue's steps, run
against the pre-fix tree, fails; run against the shipped tree, passes;
both are carried as a pins-file test. The harvest's implies cites the
red-before and the green-after. No repro, no closure claim: when the
issue ships no repro steps at all, the season states why none exists,
and the absence stays visible in the panel review.

## The skeleton

    # the season yaml declares what the season resolves (top level):
    resolves: <issue number>

    # the pins file carries the repro as a test named for it:
    def test_<unit>_issue<N>_repro_<shape>():
        """repro: <org>/<repo>#<N> -- red before the fix, green after."""

    # the harvest record's implies cites the measured shape:
    implies: issue #<N> repro red-before/green-after: <the pin's name>

## How to apply

- Rebuild the repro from the issue's own steps, never a paraphrase;
  the test's spec source is the issue text itself.
- Measure red against the unpatched tree before the fix lands, and put
  the measurement where the campaign can see it (pins header or notes).
- The harvest implies cites the red-before and the green-after with
  the pin's name; a green-only citation is not closure.
- When the issue ships no repro steps, the season states why none
  exists in the pins header and the harvest implies; the panel review
  still carries `repro: absent`. Stated absence beats silent absence;
  the panel weighs it.
- The panel input surfaces the fact, not the judgment: `rumpun`'s
  panel.claim_set reads `resolves:` and scans the pins tree, so the
  review text carries `repro: present <file>::<test>` or
  `repro: absent`. Autonomy stage decides what the flag blocks.
- The issue itself stays open to its filer. The contract is a standard
  the campaign holds itself to, not a fix that closes anything.
