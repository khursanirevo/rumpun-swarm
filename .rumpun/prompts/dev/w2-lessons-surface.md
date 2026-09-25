# s129 w2 — the lessons file becomes a first-class read

The sibling seeded .rumpun/lessons.md; the s124 disclosure said read
it before composing briefs. The report index should say it exists.

## Ground truth (measured 2026-09-20)
- the file: .rumpun/lessons.md (untracked, sibling-owned; entries are
  short lesson lines)
- the surface: src/rumpun/report.py render_index (the s113 marks and
  the s124 stall marks are the precedents; the M1 contract: persisted
  files only, identical bytes produce identical pages)
- the honest shape: present -> the index renders the entry count;
  absent -> byte-identical page (silence, not an empty promise)
- fixture discipline: tmp campaigns; synthesize the lessons file; no
  real writes

## Task
1. Land the surface: the report index renders a lessons cell (the
   entry count) when .rumpun/lessons.md exists; absent, the page is
   byte-identical. Pins red-first in
   tests/test_s129_lessons_surface.py (tmp fixtures).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/report.py, tests/test_s129_lessons_surface.py
  only. notes.md REQUIRED.
