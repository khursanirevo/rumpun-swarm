# s45 w2 — the yaml key renames, citation prefix, glossary, pins

You are w2 in season s45 (repo root: the parent of this .rumpun tree). Read
src/rumpun/lint.py, src/rumpun/scaffold.py, src/rumpun/cli.py (init), and
the operator's rename confirmation (the direct ledger). You own tests/,
scaffold.py, lint.py's key parsing, and the glossary; w1 owns the path
renames. FILE TOOLS directly. WRITE ONLY inside your workspace.
40 minutes.

## Deliverables

1. The yaml key rename: benih -> writers (scaffold.py's template output,
   lint.py's key parsing — accept BOTH keys on read for the historical
   seasons' yamls, emit writers on init).
2. The citation prefix: lint.py's citation resolver accepts akar: (the
   45 historical seasons' citations) AND ledger: (the new prefix); new
   seasons may use either; the glossary documents ledger: as preferred.
3. scaffold.py: init emits seasons/ (not musim/) and ledger/ (not akar/)
   directory names in its templates and structure.
4. GLOSSARY.md: old -> new mapping (benih/writers, musim/seasons,
   akar/ledger, rimba/runs, akar: prefix/ledger: prefix), with one line
   each on what the term means.
5. Pins (tests/ additions-only, red against current code):
   - init scaffolds seasons/ and ledger/ (not musim/, akar/)
   - a writers-keyed season lints clean; a benih-keyed historical
     season still lints clean (the alias)
   - a ledger: citation resolves; an akar: citation still resolves
   - GLOSSARY.md exists and maps every renamed term
6. Regression: the 188-test suite stays green.

## Constraints

- tests additions-only vs the current repo file (188 tests kept).
- scaffold.py + lint.py patches as workspace copies + notes.md anchors
  (the harness merges).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify engine.py, report.py, audit.py, harvest.py, evolve.py,
  cli.py, tools/ — w1 owns the paths; the harness owns cli wiring.

## Verify before finishing

Measured red set against current code in notes.md; the 188 existing
tests green.
