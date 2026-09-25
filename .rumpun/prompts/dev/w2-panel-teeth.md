# s75 w2 — the panel gets teeth (issue #1, third slice)

The panel speaks (s73) and seals verdicts. This slice makes a verdict
VISIBLE where the operator looks: a non-WIN panel verdict surfaces as
a NEED HUMAN card on the kanban board.

## Ground truth
- panel.py: request_review seals panel-<sid> (pending) then
  panel-<sid>-verdict (status: WIN/...) or panel-<sid>-error
  (status: pending, error quoted) — the akar recovery convention
- kanban.py renders NEED HUMAN from existing state: _cap_cards,
  _containment_cards, _directives_cards; render() consults
  board.pickup inside try/except (the s69 seam)
- kanban records the shape precedent: every card carries the four
  sentences (what happened / what needs doing / why a human / what
  happens if nobody acts)

## Task (spec-first, pins in tests/test_s75_w2_pins.py, _s75w2_ prefix)
1. panel.py grows: latest_panel(root, sid) — the newest
   panel-<sid>* record's status via the recorded lookup; None when
   none. Pure ledger reading.
2. kanban.py grows _panel_cards(root): for the newest closed season
   with a non-WIN panel verdict, one NEED HUMAN card with the four
   sentences (what the panel said, what needs doing, why a human
   weighs it, what happens if nobody acts). WIN verdicts render no
   card. The card cites the record id.
3. Pins: latest_panel over fixture records (WIN/LOSS/pending/error);
   the card renders only for non-WIN; kanban still degrades when
   board.pickup raises (the s69 pin stays green).
4. cli.py untouched unless the wiring demands it; keep the seams
   pluggable.

## Bounds
- Edits: src/rumpun/panel.py, src/rumpun/kanban.py, tests/. notes.md
  REQUIRED. No real route call; no .rumpun state edits.
