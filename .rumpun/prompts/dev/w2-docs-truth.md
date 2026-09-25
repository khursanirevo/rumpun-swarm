# s118 w2 — the changelog states the version truth

The close protocol's step 6 says to move [Unreleased] into a dated
section every close; the clause has been skipped all segment. The
changelog lags; a pin should say so loudly until it cannot.

## Ground truth (measured 2026-09-20)
- CHANGELOG.md: the schema-version table at the top; the dated-section
  discipline unpracticed this segment (the protocol clause is real)
- README.md: the feature surface lags ten feature seasons (the epics
  marks, the dissent, the sweep, the gate, the adjusted rollup)
- pyproject.toml: the version bumped at every close (0.16.0 through
  0.22.0 this segment)
- the docs-truth rule: the changelog's newest dated section names the
  current package version; a pin fails while they diverge

## Task
1. Bring the docs to truth: dated changelog sections through the
   current version naming the landed ships one line per season (the
   DESIGN last-five tables are the source), the readme's feature
   surface current. Land the pin: tests/test_s118_docs_truth.py
   red-first - it fails while the changelog's newest version differs
   from pyproject's, and passes once the sections exist (the pin is
   the permanent guard the skipped clause never had).
2. Verify: the pin red on the pre-fix state (capture it), green after;
   full suite green vs the known reds (solo-run any new red); ruff
   clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: CHANGELOG.md, README.md, tests/test_s118_docs_truth.py only.
  notes.md REQUIRED.
