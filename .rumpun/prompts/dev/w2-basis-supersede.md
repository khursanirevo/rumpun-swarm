# s105 w2 — the assessment basis-superseding convention (the s104 disclosed miss)

The s104 assessment's yaml omitted the top-level basis key; the module
carried its default line; the pause-and-go lived in a front instead.
The sealed record never deletes — the superseding path needs a
recorded convention. Your lane: that convention, landed and pinned.

## Ground truth (measured 2026-09-18)
- the s104 w1 disclosed miss: the module's default basis carried (the
  pause-and-go lived in the first front); a superseding basis needs an
  operator directive or a recorded re-seal convention
- the module: audit.py's seal_usefulness_assessment (the basis is a
  parameter); the akar discipline: sealed records never deleted
- the s87/s97/s98/s101/s104 records: the assessment history (five
  records, the basis lines varying)

## Task
1. Land the convention: seal_usefulness_assessment grows the
   supersede path — a re-seal with a corrected basis appends a
   superseding record (usefulness-<sid>-basis, the akar discipline:
   the original stands, the superseding record carries the corrected
   basis and cites the original), read_usefulness_assessment returns
   the superseding basis when present.
2. Pins (tests/test_s105_w2_pins.py, _s105w2_ prefix, offline): the
   re-seal appends (the original intact, the superseding record
   cites it); read_usefulness_assessment prefers the superseding
   basis; a re-seal without a basis change refuses (no noise).
3. The convention documented in the module's docstring and RESUME's
   assessment line (one clause).
4. notes.md REQUIRED: the convention, the pin map.

## Bounds
- Edits: src/rumpun/audit.py, .rumpun/RESUME.md (one clause), tests/.
  notes.md REQUIRED. No live seal call (the pins are fixtures).
