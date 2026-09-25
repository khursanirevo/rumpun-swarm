# s112 w2 — the member render names the dissent

Ten panel verdicts now exist (six pre-gate, four from the 2026-09-20
sweep: s69 LOSS, s79 NEUTRAL, s83 INCONCLUSIVE, s84 WIN). Where the
second opinion diverges from the judge, the render should say so - the
campaign reads its own disagreement.

## Ground truth (measured 2026-09-20)
- the render: src/rumpun/epics.py - the s110 basis line, the s111 panel
  mark (panel-<sid>-verdict@<sha8>, highest generation wins)
- the judge side: season_verdict() reads the last runs/<sid>/
  verdicts.jsonl row naming sid (epics.py:124); the panel side: the
  panel-<sid>-verdict record's status line
- the known dissents over the real ledger: s69 judge NEUTRAL vs panel
  LOSS; s76 panel WIN with the fallback clause vs its judge; s83 panel
  INCONCLUSIVE vs its judge WIN; s79 NEUTRAL vs judge WIN
- the s111 bounds disclosure: tests/test_s89_w2_pins.py line 252 moved
  with the render shape once already - probe the pin surface first

## Task
1. Extend the member line: when the latest panel verdict and the
   harvest verdict both exist and differ, the member line names both (a
   compact dissent mark; define the exact format and pin it). Members
   without both sides stay as they are (no invented dissents). Epic
   rows and the rollup sums unchanged. Pins red-first in
   tests/test_s112_panel_dissent.py (the s108 fixture pattern; embed
   fixture records, never copy .rumpun/runs/).
2. Verify over the real campaign: s69 and s79 (and any other true
   divergence) carry the dissent mark; non-divergent members stay bare;
   full suite green vs the known reds (solo-run any new red); ruff
   clean.
3. notes.md REQUIRED before ending the turn: the render lines, the pins
   result, the suite count. Never wait on a background job at turn end.

## Bounds
- Edits: src/rumpun/epics.py, src/rumpun/cli.py (the epics verb only),
  tests/test_s112_panel_dissent.py only. notes.md REQUIRED.
