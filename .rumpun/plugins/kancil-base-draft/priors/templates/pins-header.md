# The pins file header

## What it is

A pins file opens with the contract it pins: the band clauses it covers,
the spec sources by record id and digest, the interface it declares for
the implementer, and the measured red set. The header is the reference
both sides reconcile against at merge.

## The skeleton

    '''<suite> pins — <what is pinned> (spec-first, red today).

    The band this file pins: <the clauses, verbatim from the season
    declaration>.
    Spec sources: <the season yaml>, <the evidence records>, the
    declared interface.
    Pinned interface (declared for the implementer; reconcile at graft):
    - <verb or function>: <the exact contract>.
    Leak classes banned from the content: <the publish rules that apply>.

    Every pin fails on its own assertion, never on an escaping
    exception.
    '''

## How to apply

- Declare the interface before implementation exists; reconcile at
  merge, with evidence, when the readings diverge.
- Name the measured red set; pins that were never red test nothing.
- Helpers carry a unit-local prefix so nothing collides at merge.
