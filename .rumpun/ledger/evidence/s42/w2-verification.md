# s42 w2 — independent verification of the decade-4 usefulness audit

Scope: decade contract, F7 retirement, triage sampling, decade-3 closure ledger.
All checks re-run by w2 on 2026-09-15. Real ledger read-only; fresh audit ran in scratch.

## 1. Decade contract vs the real ledger

| Check | Result |
|---|---|
| Record exists | `2026-09-15_usefulness-decade-4.md` in `.rumpun/akar/`, appended 11:12 |
| Parsed verdict | `verdict: PARTIALLY USEFUL (different-model decade audit, route gpt-6-astra)` — token ∈ {USEFUL, PARTIALLY USEFUL, SELF-LOOP DOING NOTHING} |
| Decade fields | `decade: 4`, `seasons: 43 musim seasons at audit time` |
| Evidence pointer | `evidence: akar/evidence/usefulness-decade-4/output.txt` — file exists (3043 bytes; stderr.txt 122558 bytes) |
| Evidence sha256 | recomputed `1fe6ecec8e6c99c1cbc05c9aad4fe80ae9079c244648ed7529b567f6986d6d59` — matches the record line |
| Residuals | 21 bounded residual lines |

## 2. F7 retirement — fresh audit in a scratch copy

Before (real ledger, audit-31 at s42 seeding): `F7 usefulness decade: usefulness audit due for decade 4 (different-model review) — 42 musim seasons, 3 usefulness-decade records on the ledger`

After: snapshot rsync'd into `w2/scratch` (excluded .git, .venv, caches, w2), then `uv run rumpun audit --corpus` from the scratch root. Exit 0. It appended audit-32 to the scratch akar plus a fresh replay-matrix.md inside scratch. Real ledger gained nothing: 0 audit-32 records in the real akar.

Result: the fresh run prints F1-F6 and the corpus line; no F7 line in stdout or in the scratch audit-32. 43 musim seasons owe floor(43/10) = 4 decades; 4 records cover them — the finding's fixed point (`_usefulness_decade_due`, src/rumpun/audit.py:283).

F-lines verbatim (scratch audit-32):
`F1 phase liveness: phase execute (writes results.jsonl) wrote its artifact in 8 of 8 engine seasons (s34,s35,s36,s37,s38,s39,s40,s41,s42)`
`F1 phase liveness: phase evaluate (writes verdicts.jsonl) wrote its artifact in 8 of 8 engine seasons (s34,s35,s36,s37,s38,s39,s40,s41,s42)`
`F2 stall recurrence: stopped_stall in 0 of 9 seasons with state.json (none); recurrence no (threshold 2)`
`F3 verdict histogram over verdicts.jsonl of s34,s35,s36,s37,s38,s39,s40,s41 (none in: s42): WIN 28, LOSS 1, INVALID 2`
`F4 route outcomes: route fable: 14 clean-deliverable, 0 clean-empty, 0 failed, 2 not-exited over 16 spawns (s34,s35,s36,s37,s38,s39,s40,s41)`
`F5 band calibration: no LOSS season shipped integrated modules (s34,s35,s36,s37,s38,s39,s40,s41)`
`F6 budget compliance: campaign_cost_cap unset since campaign start (P9) — operator sets the number; the tool only flags`
`corpus: fresh matrix, 5 PASS, 0 FAIL, 1 DRIFT, 80 SKIP — all green on main, no candidates`

Suite: 188 passed in 74.97s, exit 0 (`uv run pytest -q`, scratch copy) — 188 ≥ the 171 floor the season brief names. No code changed this season.

## 3. Closure ledger — usefulness-decade-3 residuals

Statuses (amended in §5): 4 CLOSED, 6 PARTIAL, 11 OPEN (21 total). "PARTIAL" = the named defect got a mechanism, the residual's stronger claim stands.

| # | Decade-3 residual (abridged) | Status | Closer / w2 evidence |
|---|---|---|---|
| R1 | External task value unmeasured | PARTIAL — s37 (re-armed by d4 #3; see §5) | `tools/coldstart_check.py`: documented quickstart verified end to end from cold start; DESIGN s37 records the closure |
| R2 | Ledger gives verdict labels, not implementation correctness | PARTIAL — s35 (re-armed by d4 #8, #18; see §5) | run_audit arms WIN-with-FAIL-rows mismatch candidates (src/rumpun/audit.py:783); DESIGN s35: "closed in code" |
| R3 | Headline 34 seasons vs 33 identifiers | CLOSED — s39 | `season_split` reports run vs drafted-only in the decadal brief (tools/usefulness_audit.py); DESIGN s39: "closed at the source" |
| R4 | s1 and s33 lack verdicts; count overstates assessed work | CLOSED — s39 | same split; drafted-only never inflates the run count |
| R5 | s30/s32 record WIN despite stopped_stall | OPEN | No salvage-value vs execution-reliability split found on the ledger; decade-4 residual 5 repeats it |
| R6 | Harness repairs do not establish autonomous completion | OPEN | decade-4 residual 17 repeats it; no autonomy measure landed |
| R7 | No unchanged control vs direct development | PARTIAL — s38 | coldstart steps 7-11 verify the loop's defining property outside the ledger ("first concrete answer"); a matched direct-development control still absent; decade-4 residual 2 repeats |
| R8 | Campaign cost cap unset | OPEN | Fresh audit F6 this run: unset since campaign start (P9); operator-owned; decade-4 residual 13 repeats |
| R9 | Historical bands obscure shipped value | OPEN | Band-mask guard is warning severity only (src/rumpun/lint.py:412-414); decade-4 residual 9 repeats |
| R10 | s32 adds a warning, not mandatory rejection | OPEN | Source check: lint.py:412-414 emits Finding("warning"), no error path — residual accurate against current main |
| R11 | Sustained beneficial graph evolution unproven | OPEN | Pipeline still execute→evaluate; one trim (s12) on the ledger, no second mutation |
| R12 | falsify_required was a words-only invariant | CLOSED — s34 | lint errors when falsify_required is declared with no artifact-reading phase (src/rumpun/lint.py:335-344); DESIGN s34: "sharpest residual, closed" |
| R13 | Phase-2 goal change vs goal_immutable | PARTIAL | Operator order on record (DESIGN §15, 2026-09-14); no invariant-migration record; decade-4 residual 15 repeats |
| R14 | Rollback never runs git | OPEN | By design: src/rumpun/evolve.py:17 — "code-level restore is an explicit git revert by the operator"; decade-4 residual 16 repeats |
| R15 | Evaluator independence lacks recurring enforcement | CLOSED — s33 | The s33 mechanism fired on schedule: audit-31's F7 seeded s42 and decade-4 landed mid-season — the first scheduled firing is the demonstration |
| R16 | 6 corpus scripts pass, 47 skipped | OPEN | Fresh matrix this run: 5 PASS, 1 DRIFT, 80 SKIP of 86 discovered — coverage still a minority, skips carry reasons |
| R17 | DRIFT and malformed-row handling unestablished | PARTIAL — s26 | Malformed rows get skip classes (src/rumpun/audit.py:480); DRIFT arms nothing (audit.py:690-695: FAIL/REGRESSION only); fresh run: 1 DRIFT, no candidate |
| R18 | Appended log bytes are not durable progress | OPEN | s24 fixed touch-only; the growth rule itself is unchanged; decade-4 residual 12 repeats |
| R19 | Same-identity observation gives no tamper resistance | OPEN | Documented threat-model limit (DESIGN §13); no mechanism change on the ledger |
| R20 | Premature review-closure claims | PARTIAL — s41 | The named premature claim (M4 "review fully retired") closed in full by s41; decade-4 residual 14 asks for explicit historical correction |
| R21 | No marginal-value stop rule | OPEN | Operator standing order vs codex-usefulness "operator decides"; decade-4 residual 21 repeats |

Cross-check: 12 of decade-4's 21 residuals restate surviving decade-3 items (control baseline, cost cap, warning-not-rejection, corpus coverage, appended-byte progress, goal-after-lock, rollback, autonomy, stall verdict totals, stop rule, evaluator semantics, prevention-vs-repair). The fresh different-model review independently agrees with this ledger on what stays open.

Closure evidence basis: every row checked by w2 this session against source (lint.py, audit.py, evolve.py, tools/), the akar records (audit-31, codex-usefulness, harvests), and DESIGN §15-16. DESIGN say-so alone was not accepted where a source line exists.

## 4. Sample verification of w1's triage (3 picks + 1 bonus, each on my own evidence)

| w1 ruling sampled | w1 decider | w2 re-check (independent read) | w2 verdict |
|---|---|---|---|
| #9 s32 guard warns, not rejects — confirmed | lint.py:32-37, 213-215 | Same lines read fresh: BAND_MASK_TOKENS at lint.py:37, warning text at :213-215, emitted via warn() at :412-414 (Finding "warning", no error path) | CONFIRMED — ruling and citation accurate |
| #15 goal changed after lock — refuted | DESIGN:875-878; scaffold.py:30 | DESIGN.md:875-878: "## 15. Campaign phase 2 — self-evolution (operator order 2026-09-14)" and "rumpun.yaml updated accordingly"; scaffold.py:30: "# panel cannot waive". The operator order sits inside the brief the reviewer read. | REFUTED correctly — the authorization is on the record |
| #20 census 43 vs enumeration s1-s42 — refuted as inconsistency | s43 drafted-only; season_split | Counted myself: 43 musim yamls, 42 rimba dirs; musim/s43.yaml header "drafted by evolve v0 from s42"; season_split counts drafted-only separately. Membership reconciles. | REFUTED correctly — presentational gap only |
| #7 s34 falsify gate weak — confirmed (bonus) | lint.py:328-345 | Read fresh: the gate errors only when NO phase reads an artifact (:335-345); the stronger reachability rule (:317-325) needs a falsify node, absent since the s12 trim | CONFIRMED — claim accurate |

Cross-checked: w1's cost-cap citation (rumpun.yaml:19, `campaign_cost_cap: null`) matches the file.

## 5. Addendum — ledger amended after cross-reading w1's triage

- R1 and R2 move CLOSED → PARTIAL: the decade-4 reviewer re-arms both cores (d4 #3 external task quality; d4 #8 + #18 semantic correctness). My original CLOSED rested on DESIGN say-so (s37, s35) that the fresh different-model review disputes. Amended tally: 4 CLOSED (R3, R4, R12, R15), 6 PARTIAL (R1, R2, R7, R13, R17, R20), 11 OPEN.
- Kept differences from w1's ledger, not copied: R13 — w1 refutes entirely (the operator waives); I keep PARTIAL (authorization on record at DESIGN:875-878, but no formal invariant-migration record, and the reviewer repeated the residual after reading that same brief). R17 — w1 rules open; I keep PARTIAL — s26 (malformed-row skip classes exist at audit.py:480; the DRIFT half is open in both ledgers). Every other row agrees across lanes.

Suite constraint note: w1's live-tree run reports 187/188 — the s38 isolation pin (test_rumpun.py:5889) trips on this season's own harness lane writes. Cause read and verified by w2 at tests/test_rumpun.py:5746,5765: the volatile exclusion hardcodes rimba/s38/**, the live season as of s38. My 188/188 ran in a static scratch copy, where no live writes land mid-window; both observations are consistent. Pre-existing latent defect; w1 drafted the handover candidate in its notes.
