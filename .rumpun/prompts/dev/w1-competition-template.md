# s127 w1 — the competition season stays one command away

The operator may point the campaign at an external workload; the
scaffold already emits the competition-season shape. Pin it so the
path stays real.

## Ground truth (measured 2026-09-20)
- the template: .rumpun/seasons/_competition.yaml (the scaffold emits
  it per docs/campaign-guide.md's table)
- the gate: rumpun lint .rumpun/seasons/<yaml> - the filled shape must
  lint clean; the bare FILL-marker shape refuses with named errors
  (the positive control: prove the gate fires before trusting the
  pass)
- the guide's competition claims: docs/campaign-guide.md names the
  template and the path
- fixture discipline: init in tmp campaigns; the real campaign never
  written in tests

## Task
1. Pin the shape: a filled competition yaml lints clean, and the bare
   template's refusal names its errors (both sides pinned - the
   positive control is the bare-template refusal). Align
   docs/campaign-guide.md's competition section with the template's
   actual fields. Pins red-first in
   tests/test_s127_competition_template.py (tmp campaigns).
2. Verify: solo pins green; full suite green vs the known reds
   (solo-run any new red); ruff clean.
3. notes.md REQUIRED before ending the turn (the gate watches now).
   Never wait on a background job at turn end.

## Bounds
- Edits: .rumpun/seasons/_competition.yaml (only if the template
  itself needs a fix), docs/campaign-guide.md (the competition
  section), tests/test_s127_competition_template.py only. notes.md
  REQUIRED.
