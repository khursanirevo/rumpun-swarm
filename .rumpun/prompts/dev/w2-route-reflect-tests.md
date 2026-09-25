# Task: spec-first tests for the audit extensions (full test file into workspace)

Workspace: /mnt/data/work/rumpun/rimba -- corrected workspace:
/mnt/data/work/rumpun/.rumpun/rimba/s13/w2. Write ONLY test_rumpun.py,
notes.md, lane_tool.py into this workspace. Do not touch anything outside it.

Base your test_rumpun.py on the CURRENT repo file
/mnt/data/work/rumpun/tests/test_rumpun.py (read it first; keep all 41
existing tests passing).

The audit extension lands at integration. New behavior (spec; author against
exactly this):
- Per-route outcome finding: for each route over audited engine seasons,
  a line "route R: A clean-deliverable, B clean-empty, C failed, D
  not-exited over N spawns" citing season ids. Outcome classes: exit 0 +
  deliverable (any non-bookkeeping file in the agent workspace, recursive)
  = clean-deliverable; exit 0 without = clean-empty; non-zero exit = failed;
  other state = not-exited. Bookkeeping set: agent.log, exit, prompt.md,
  prompt-meta.yaml, state.json, terminated, terminated.tmp, __pycache__.
- Candidate when a route has >= 2 clean-empty: text contains "clean-empty"
  and "tool-check" and the route name.
- Band calibration: a harvested season whose verdict is LOSS with >= 1
  results.jsonl row "integrated": true yields "band masked value" naming the
  season; >= 2 such seasons yield a "recalibrate LOSS bands" candidate.
- Budget flag: rumpun.yaml without campaign.budget.campaign_cost_cap yields
  the "campaign_cost_cap unset" finding (finding only, never a candidate).
- Priority under MAX_CANDIDATES = 3 unchanged: phase triggers first, then
  route, then calibration; budget is finding-only. musim/ and rimba/ remain
  byte-identical after run_audit.

Add, at minimum (extend the AUDIT fixture builder with workspaces and
results rows):
1. Two routes with distinct outcome mixes -> both route lines present with
   the right counts, seasons cited.
2. A route with two clean-empty spawns -> the tool-check candidate fires.
3. One LOSS season with one integrated row -> "band masked value" finding,
   no recalibrate candidate; second such season -> candidate fires.
4. Missing campaign_cost_cap -> the budget finding appears.
5. run_audit immutability on the extended fixture (musim/rimba unchanged).

Collab lane (protocol v2, NON-BLOCKING): post kind=start, kind=policy,
kind=done via lane_tool.py from the env vars. Never wait on w1.

Rules: pytest only; no skips; no mocks. ruff clean, line-length 100,
py3.10+. notes.md: what you added, what you left out.
