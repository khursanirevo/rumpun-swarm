# s129 w1 — every parser flag is named or hidden on purpose

The s128 lane proved the verbs named; the reverse direction was left
standing: parser flags the readme table never mentions.

## Ground truth (measured 2026-09-20)
- the named drift: board --mirror, audit --dry-run, check --out-dir,
  init --plugin exist on the parser and appear in no readme row
- the table: README.md's verbs table (26 rows, the s128 parser pin
  guards the forward direction)
- the honest shape: a flag is either named in its row or documented as
  intentionally hidden (a footnote naming the hidden set) - both are
  truthful; silence is not
- fixture discipline: read-only pins; no writes anywhere

## Task
1. Land the audit: every parser flag named in its readme row or in the
   intentional-hide footnote; drift (a flag in neither) fails naming
   it. Pins red-first in tests/test_s129_reverse_flag_audit.py.
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: README.md, tests/test_s129_reverse_flag_audit.py only.
  notes.md REQUIRED.
