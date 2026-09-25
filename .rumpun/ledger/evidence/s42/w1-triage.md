# s42 w1 — decade-4 usefulness audit: run + residual triage

## Run (observed)

- Runner: `.venv/bin/python tools/usefulness_audit.py` from repo root, finished 2026-09-15 11:12:38, exit 0 (`audit-run.log` in this workspace).
- Record: `.rumpun/akar/2026-09-15_usefulness-decade-4.md`, verdict **PARTIALLY USEFUL**, 21 residuals, read back in full.
- Evidence: `akar/evidence/usefulness-decade-4/output.txt`, sha256 in the record (`1fe6ecec…`). Raw route output stays in evidence; only the verdict and residual lines are reproduced below.
- Census at audit time: 43 musim yamls, 41 run, 2 drafted-only (s1: no state file; s43: no rimba dir). s43's goal names this audit; the runner landed it inside s42's window.

## Verdict + residuals (verbatim, extracted from the record)

VERDICT: PARTIALLY USEFUL

1. Locking fixes, containment, honest exits, and reduced rendering establish concrete utility. Their net benefit lacks measured operating costs.
2. No matched control compares this loop with direct implementation on equivalent tasks, budgets, and acceptance criteria.
3. Stub-model cold starts demonstrate workflow integration. They establish neither external task quality nor autonomous improvement.
4. Manual repairs repeatedly complete interrupted or incorrect submissions. Reported wins do not isolate agent output from this intervention.
5. s30 and s32 record WIN after stopped_stall and subsequent integration. Verdict totals therefore cannot measure reliable season completion.
6. s37 records WIN with a deferred production clause. Conditional acceptance leaves stall-resume effectiveness unproven in production.
7. s34 accepts any artifact-reading phase as falsification. This does not enforce sealed predictions, meaningful rejection criteria, or evaluator independence.
8. s35 detects WIN alongside explicit FAIL rows. Missing, incorrect, or uniformly optimistic results still escape this consistency check.
9. s32 warns about undefined integration bands. A warning does not prevent vague bands or unsupported WIN judgments.
10. The corpus runs six reproduction scripts while skipping 47 discovered scripts. Coverage of every ratified behavior remains unsupported.
11. Appended log bytes count as stall progress. Repeated output can therefore mask absent durable work despite the design contract.
12. s36 increases budgets after stopped_stall. Longer budgets do not repair provider hangs, session teardown, or the stall detector.
13. The campaign cost cap remains unset in the supplied account. Aggregate spending and operator repair time remain unreported.
14. “All findings closed” predates s41’s full M4 repair. Closure records overstate completeness and require explicit historical correction.
15. The phase-2 account changes the campaign goal after its declared lock. No invariant-preserving migration appears in the brief.
16. Rollback records containment and explicitly never runs git. Restoration to the promised last-good code state remains unsupported.
17. Manual-stage delivery does not demonstrate the proposed panel governance, automatic containment, or earned autonomous operation.
18. Different-model reviews still share campaign-selected evidence. Harness observation of verdict rows does not establish their semantic correctness.
19. Missing notes and write corruption recur. Recovery demonstrates useful repair capacity without demonstrating prevention.
20. The census reports 43 seasons, but the verdict enumeration names only s1–s42. The supplied inputs do not reconcile membership.
21. Continuous operation lacks an evidenced stopping threshold for marginal value. Internally generated residuals can sustain work after practical needs settle.

## Residual triage (21/21)

Rulings: confirmed = the residual holds against today's source and ledger. refuted = the ledger or source decides against it.

| # | Residual (short) | Ruling | Decider |
|---|---|---|---|
| 1 | Utility without measured operating costs | confirmed | `rumpun.yaml:19` (`campaign_cost_cap: null`); `src/rumpun/audit.py:678` (F6 finding). Durations are measured per season (harvest rows carry duration); no aggregate or repair-time accounting exists. |
| 2 | No matched control | confirmed | No control exists anywhere. `tools/coldstart_check.py` runs a stub model (`tools/coldstart_check.py:10,57-59`); s38's loop-check is workflow verification, not a matched comparison. |
| 3 | Stub cold start ≠ task quality | confirmed | `tools/coldstart_check.py:57-59`: the stub appends one fixed results row, exit 0. A fixed stub cannot demonstrate task quality or autonomous improvement. |
| 4 | Manual repairs complete interrupted work | confirmed | `rimba/s30/verdicts.jsonl` season row: "harness repaired + completed the salvage"; `rimba/s32/verdicts.jsonl`: "stopped_stall at 1653s ... verified on main posthumously"; DESIGN s41 entry: "s40's scope, resumed and landed in one cycle". |
| 5 | Verdict totals can't measure reliability | confirmed | Same two season rows: both WINs stand in the F3 histogram despite the recorded stall/salvage. |
| 6 | s37 deferred production clause | confirmed | DESIGN s37 row: "stall-resume production clause deferred - no triggering event"; `s37-harvest` implies line. No stall occurred s38-s41 (s40 was teardown-kill), so production exercise is still pending. |
| 7 | s34 falsify gate is weak | confirmed | `src/rumpun/lint.py:328-345`: the gate errors only when no phase's `reads` names an artifact; any single reader satisfies it. The stronger reachability rule (`lint.py:317-325`) needs a falsify node; the pipeline has none since s12. No sealed predictions. |
| 8 | s35 mismatch check has gaps | confirmed | `src/rumpun/audit.py:765-790`: arms one candidate only for a WIN season whose results rows carry explicit FAIL; code comment: seasons without results rows are out of scope. DRIFT arms nothing (`audit.py:704-706` arms FAIL/REGRESSION only; DRIFT appears only in the count line). |
| 9 | s32 guard warns, does not reject | confirmed | `src/rumpun/lint.py:32-37,213-215`: token check on `expected_band`; the s32 season row itself says "lint warns". A vague band holding the right tokens passes. |
| 10 | Corpus skips most scripts | confirmed; numbers stale | Today's `audit-31` corpus line: 5 PASS, 0 FAIL, 1 DRIFT, **80 SKIP**. The residual's 6/47 figures are the s25-era account from DESIGN; the substance (most scripts skip) holds and worsened. |
| 11 | Appended bytes count as progress | confirmed | `src/rumpun/engine.py:439`: "appended bytes: durable progress now". Growth past `last_size` defeats detection by design (the M10 trade-off). |
| 12 | s36 budgets don't repair | confirmed | `src/rumpun/evolve.py:92-164`: ceil(parent × 1.5) budgets plus a stall citation line. It resumes; it does not repair hangs, teardown, or the detector. s36's own claim (one-cycle stall cost) holds. |
| 13 | Cost cap unset | confirmed | `rumpun.yaml:19`; `src/rumpun/audit.py:678`. |
| 14 | Closure overstatement predates s41 M4 | confirmed; remediated for M4 | DESIGN:1235 ("Full accounting ... M1-M11 (s21-s24)") predates the reopening. s41 closed M4 in full (`src/rumpun/harvest.py:98,134-141`: `_is_terminal` fail-closed) and DESIGN's s41 entry records the repair. Earlier lines stand unannotated. |
| 15 | Goal changed after lock | **refuted** | DESIGN:875-878: section 15 header "operator order 2026-09-14", "Phase 2 goal (rumpun.yaml updated accordingly)". The authorized transition sits inside the brief itself. The invariant binds agents (`src/rumpun/scaffold.py:30`: "panel cannot waive"); the operator is the waiving authority and ordered the change. |
| 16 | Rollback never runs git | confirmed; documented intent | `src/rumpun/evolve.py:421-423,455-456`: "this verb never runs git; code-level restore is an explicit git revert by the operator". Restoration is operator-manual by design, so autonomous restore stays unsupported. |
| 17 | Manual-stage only | confirmed | DESIGN:600 ("Staging: MVP ships manual only"); `src/rumpun/audit.py:5-6`: candidates pass only the evolve gate (lint plus operator at the manual stage). |
| 18 | Reviews share campaign-selected evidence | confirmed | `tools/usefulness_audit.py` `compose_brief`/`design_sections`: the brief is DESIGN 13-end plus the verdict history, all campaign artifacts. Citations stay [A] (DESIGN 13 provenance table). |
| 19 | Missing notes and corruption recur | confirmed | DESIGN s35 entry: "w2 caught four of its own write corruptions mid-season by readback"; s39 and s41 entries: "third missing-notes season for w2"; akar `harness-write-corruption`. Readback is mitigation, not prevention. |
| 20 | Census 43 vs enumeration s1-s42 | **refuted as an inconsistency** | musim holds s1-s43 (43 yamls); rimba holds s1-s42; s43 is drafted-only (`musim/s43.yaml` header: "drafted by evolve v0 from s42"). The brief headline counts s43 in "2 drafted-only" (`tools/usefulness_audit.py` `season_split`); the history section covers rimba seasons only, by stated rule (`verdict_history`). Membership reconciles: 42 enumerated + s43 counted = 43. The gap is presentational: the brief does not name drafted-only ids. |
| 21 | No stopping threshold | confirmed | DESIGN:875-876: the operator ordered the chain to never stop. No marginal-value threshold exists in code or config; the codex-usefulness record leaves pausing to the operator. |

Score: 19 confirmed (three carry notes: #10 stale numbers, #14 remediated for M4, #16 documented intent), 2 refuted (#15, #20).

## Decade-3 closing ledger (21/21)

| # | Decade-3 residual (short) | Status | Decider |
|---|---|---|---|
| 1 | External task value unmeasured | partially closed | s37/s38 closed the workflow form (coldstart checker, steps 1-11); the stub cannot measure task value, so the residual's core re-arms in decade-4 (#3). |
| 2 | Verdicts ≠ correctness | partially closed | s35's mismatch candidates (`audit.py:765-790`) arm on WIN+FAIL; the wider semantic claim re-arms in decade-4 (#8, #18). |
| 3 | 34 counted vs 33 identifiers | **closed by s39** | `season_split` in `tools/usefulness_audit.py`; s39-harvest implies line. |
| 4 | s1/s33 lack verdicts | **closed by s39** | The brief now splits run vs drafted-only; `verdict_history` marks s1 "none" honestly. s33/s34 ran after the audit. |
| 5 | s30/s32 WIN despite stall | open | decade-4 #5. |
| 6 | Autonomy unproven | open | decade-4 #4. |
| 7 | No baseline | partially closed | s38's loop-verification (checker steps 7-11) is the first external check that reflection seeds the next cycle; a matched control still does not exist (decade-4 #2). |
| 8 | Cost cap unset | open | decade-4 #13; `rumpun.yaml:19`. |
| 9 | Bands obscure value | open | decade-4 #1, #9. |
| 10 | s32 warning not gate | open | decade-4 #9; `lint.py:213-215`. |
| 11 | Graph evolution unproven | open | No decade-4 restatement; s34-s41 exercised no structural mutation, so the item stands unexercised. |
| 12 | falsify removed vs falsify_required | **closed by s34** | `lint.py:328-345` (enforced when the invariant is declared); s34-harvest implies line. |
| 13 | goal_immutable conflict | **refuted** | Same as decade-4 #15: the operator order at DESIGN:875-878 authorizes the transition. |
| 14 | Rollback never runs git | open (by-design) | `evolve.py:421-423`; decade-4 #16. |
| 15 | Panel governance undemonstrated | open | DESIGN:600; decade-4 #17. |
| 16 | Corpus skips most scripts | open | audit-31: 80 SKIP; decade-4 #10. |
| 17 | DRIFT/malformed rows arm nothing | open | `audit.py:704-706`, `audit.py:765-790`. s35 added verdict-vs-artifact mismatch, not DRIFT handling. |
| 18 | Log bytes as progress | open | `engine.py:439`; decade-4 #11. |
| 19 | Shared identity, no tamper resistance | open | DESIGN 13 threat model states the limit; decade-4 #18. |
| 20 | Premature closure claims | partially closed | The M4 case is repaired in fact (s41, `harvest.py:98,134-141`) and re-accounted in DESIGN's s41 entry; the pattern remains unenforced-against. decade-4 #14. |
| 21 | No stop rule | open | decade-4 #21; DESIGN:875-876. |

Ledger total: 3 closed (two by s39, one by s34), 1 refuted (#13), 4 partially closed (#1, #2, #7, #20), 13 open.

## Suite constraint (deviation reported)

- Full suite: **1 failed, 187 passed** (65.34s, `pytest.log`). Solo re-run of the failing test: same single failure (12.94s, `pytest-solo.log`).
- Failing: `test_s38_coldstart_checker_leaves_repo_rumpun_untouched` (`tests/test_rumpun.py:5889`).
- The checker itself passes 11/11 (exit 0, in the pin's own assertion message). The snapshot's only deltas are `.rumpun/rimba/s42/w1/agent.log` and `state.json` — this season's own harness writes during the pin's snapshot window.
- Cause (read at the code): `_s38_rumpun_snapshot` (`tests/test_rumpun.py:5746`) hardcodes the volatile exclusion to `rimba/s38/**` (`tests/test_rumpun.py:5765`) — the live season as of s38, stale since s39. The docstring states the intent as "the live season's own lanes". Running the suite from a live season ≥ s39 trips the pin whenever the season's harness writes its own lanes mid-window. Why s39-s41 stayed green is unconfirmed; the exclusion has been stale since s39.
- This season changed no code; the red pin is a pre-existing latent defect exposed by running the suite inside a live season. The constraint "the 171-test suite stays green" does not hold today as stated: 187/188 with the cause above.

### Draft candidate (handover; no code changed by w1)

```
The s38 isolation pin fails on any live season whose harness writes its own
lanes during the pin's snapshot window. _s38_rumpun_snapshot
(tests/test_rumpun.py:5746) hardcodes the volatile exclusion to
.rumpun/rimba/s38/** (tests/test_rumpun.py:5765), the live season as of
s38, stale since s39. Replace it with a dynamic rule: exclude
rimba/<sid>/** for every sid whose rimba/<sid>/_season/state.json exists
and is non-terminal (status running/paused/unknown), matching the
docstring's stated intent ("the live season's own lanes").

Repro: run the suite from a live season >= s39;
test_s38_coldstart_checker_leaves_repo_rumpun_untouched fails with deltas
only in the live season's agent.log and state.json; the checker itself
exits 0 with 11/11 steps PASS.

Band: WIN when the pin passes from a live season with the season's own
harness writes landing mid-window, AND still trips when a checker run
mutates a non-volatile path.
```

## Checks done

- usefulness-decade-4 record exists with parsed verdict PARTIALLY USEFUL and 21 residual lines; read back in full from `.rumpun/akar/2026-09-15_usefulness-decade-4.md`; residual lines above extracted mechanically from the record.
- Triage covers 21/21 decade-4 residuals; decade-3 ledger covers 21/21, each with a decider.
- Suite: 187/188 observed (see the deviation section); solo re-run reproduced the same single failure. No code changed this season.
- ruff: no Python written this season; nothing to lint.
