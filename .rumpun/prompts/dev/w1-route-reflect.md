# Task: extend audit.py — route outcomes, band calibration, budget flag

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s13/w1. Write ONLY audit.py,
notes.md, lane_tool.py into this workspace. Do not touch anything outside it.

Base your audit.py on the CURRENT repo file
/mnt/data/work/rumpun/src/rumpun/audit.py (read it first; keep every behavior
and all 41 tests passing; do not edit tests/). cli.py should need no change —
if you find one necessary, note it in notes.md instead of editing cli.py
(harness decides at merge).

Three new deterministic findings/candidates, appended after the existing
phase-liveness triggers in the record (same cap-3 semantics: overflow named,
never invented):

1. Route outcomes (per benih, over audited engine seasons):
   - classify each agent workspace: read rimba/<sid>/_season/state.json
     agents{name: {route, state, exit_code}}; deliverable = any file in
     rimba/<sid>/<name>/ except the bookkeeping set {agent.log, exit,
     prompt.md, prompt-meta.yaml, state.json, terminated, terminated.tmp,
     __pycache__} (recursive).
   - outcome categories: clean-deliverable (exit_code 0 + deliverable),
     clean-empty (exit_code 0, no deliverable — the tool-less signature),
     failed (exit_code non-zero), not-exited (state not exited/failed).
   - finding line per route: "route R: A clean-deliverable, B clean-empty,
     C failed, D not-exited over N spawns" citing the season ids.
   - candidate trigger: a route with >= 2 clean-empty -> "route R: B
     clean-empty spawns — add spawn tool-check or prefer alternative route";
     band: "WIN when clean-empty rate drops to 0 or a tool-check lands".

2. Band calibration (per harvested season with results.jsonl):
   - integrated count = results.jsonl rows with "integrated": true;
     season verdict from the last season-level verdicts row (existing logic).
   - finding when verdict is LOSS and integrated count >= 1:
     "LOSS season <sid> shipped K integrated module(s) — band masked value",
     citing sid; candidate when >= 2 such seasons: "recalibrate LOSS bands:
     count integrated deliverables in the band" citing those seasons.

3. Budget compliance: read rumpun.yaml campaign.budget.campaign_cost_cap;
   if null/absent, finding: "campaign_cost_cap unset since campaign start
   (P9) — operator sets the number; the tool only flags".

Keep MAX_CANDIDATES = 3 with the existing pipeline-order-first priority:
phase triggers, then route, then calibration, then budget-flag as a finding
only (never a candidate). Update the module docstring's trigger list to
match. All new findings cite season ids; nothing else mutates.

Collab lane (protocol v2, NON-BLOCKING): post kind=start, kind=policy (your
exact trigger rules), kind=done via lane_tool.py from the env vars. Never
wait on w2.

Rules: stdlib only; ruff clean, line-length 100, py3.10+. notes.md: the
trigger rules, the priority order under the cap, and what you left out.
