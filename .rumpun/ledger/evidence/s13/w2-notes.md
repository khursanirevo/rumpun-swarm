# w2 s13 — spec-first tests for the audit extensions

Status: delivered. `test_rumpun.py` (based on the repo file, 41 existing tests
untouched — diff shows insertions only), `lane_tool.py` (s12 pattern, protocol
v2), this note. Nothing outside this workspace was written.

## Verification (real runs)

- `PYTHONDONTWRITEBYTECODE=1 python -m pytest .rumpun/rimba/s13/w2/test_rumpun.py
  -p no:cacheprovider -q` → **7 failed, 43 passed**. ✅ the 41 existing tests
  all pass; the 7 reds are the spec-first extension tests failing against
  current `audit.py` exactly as intended (no route/calibration/budget lines
  exist yet). The red set: per-route outcome lines, tool-check candidate,
  single masked LOSS (finding only), two masked LOSSes (candidate), budget
  finding, candidate priority, route window scope.
- `ruff check --no-respect-gitignore <workspace>/test_rumpun.py <workspace>/lane_tool.py`
  → clean (repo config: line-length 100, py310; `--no-respect-gitignore`
  because rimba/ is gitignored and a plain run checks zero files).
- `diff tests/test_rumpun.py .rumpun/rimba/s13/w2/test_rumpun.py` → only the
  additions below plus two modified lines in `_write_audit_proj` (new
  defaulted `project_yaml` param and its docstring line).

## What I added

Nine tests under `--- audit extensions (w2 s13 scope, spec-first) ---`, plus
fixture-builder extensions (`_write_spawn`, `_write_results_rows`,
`_write_harvest_record`, `RUMPUN_YAML_CAPPED`, `project_yaml` param on
`_write_audit_proj`) and a module-docstring paragraph stating the contract:

1. `test_audit_route_outcome_lines_per_route` — glm mixes all four classes
   (5 spawns incl. one crashed and one terminated, both not-exited), fable is
   pure clean-deliverable; both lines present once, exact counts, sids cited
   in the line (fable cites s2 only — a route's own evidence).
2. `test_audit_route_two_clean_empty_spawns_tool_check_candidate` — route sol,
   two clean-empty spawns across s1+s2 → one `candidate:` line containing
   "tool-check", "clean-empty", the route name, and both sids. The per-route
   test carries the below-threshold negative (glm has one clean-empty, no
   tool-check anywhere).
3. `test_audit_single_masked_loss_is_finding_not_candidate` — s1 LOSS+integrated
   → exactly one "band masked value" line naming s1; s2 LOSS without
   integration and s3 WIN with integration are not named; "recalibrate"
   nowhere.
4. `test_audit_two_masked_losses_yield_recalibrate_candidate` — two masked
   seasons → one `candidate:` "recalibrate LOSS bands" line citing both.
5. `test_audit_missing_cost_cap_is_finding_never_candidate` — "campaign_cost_cap
   unset" appears exactly once and never on a `candidate:` line.
6. `test_audit_set_cost_cap_clears_budget_finding` — `campaign.budget.
   campaign_cost_cap: 100` present → no finding (passes today; pins the key
   path for the implementation).
7. `test_audit_candidate_priority_phase_route_calibration` — all three
   triggers armed (dead evaluate phase, 2× clean-empty sol, 2× masked LOSS) →
   exactly 3 candidates in order phase → route → calibration; budget finding
   present, never a candidate.
8. `test_audit_extended_fixture_leaves_musim_rimba_untouched` — byte-identity
   of musim/ + rimba/ over the extended fixture (passes today).
9. `test_audit_route_scan_stops_at_window` — last_n=1 excludes s1's glm spawn
   from the route scan.

Contract decisions the task spec left open, pinned by these tests:

- Verdict source: a real akar `<sid>-harvest` record (written via
  `akar.append_record` in harvest.py's exact id/body shape, `verdict: LOSS`
  line) — harvest is the verdict system of record, and it decouples the
  calibration trigger from verdicts.jsonl (a phase artifact).
- Route lines: one aggregated line per route with ≥ 1 spawn over the audited
  engine seasons; exact shape `route R: A clean-deliverable, B clean-empty,
  C failed, D not-exited over N spawns`; contributing sids in the line.
- Bookkeeping set is behavioral, all 8 names exercised: the clean-empty spawn
  carries agent.log, exit, prompt.md, prompt-meta.yaml, state.json,
  terminated.tmp, a `terminated` marker (exit 0 beats the marker), and
  `__pycache__/mod.pyc` — directory name counts, so the pyc is not a
  deliverable — while `results/findings.md` (nested) is one.
- crashed (no exit file) and terminated (marker, no exit file) both classify
  as not-exited ("other state").
- Extension candidates keep the `candidate: ` prefix so `candidate_lines()`
  and the verb output keep working.

## What I left out

- CLI-level tests (`rumpun audit` argv surface) — function-level only, matching
  the s11 precedent.
- Finding-label numbering (F4/F5/…) and the citation format beyond "the sids
  appear in the line" — assertions are content substrings so the implementer
  numbers and formats findings freely.
- Route lines for zero-spawn routes (spec implies none exist).
- Corrupt-input edges for the new sources (unparsable state.json in a spawn
  workspace, harvest record without a verdict line) — current audit.py
  precedent (refuse, don't guess) presumably extends; not pinned here.
- Any implementation: audit.py, cli.py, and the repo test file are untouched.
