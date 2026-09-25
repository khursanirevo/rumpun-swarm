# s28 w2 notes

## Deliverable 1 - DESIGN.md section 16

Anchor: section "16. The external-review arc and the corpus gate (s17-s27)"
appended at the end of the workspace DESIGN.md copy, immediately after the
s27 entry that ends the source file (source ends at line 1158; section 16
occupies lines 1159-1215 of the copy). Merge = append that block to DESIGN.md.

Section title uses "## 16." to match the "## 13." / "## 14." / "## 15."
house style; the brief wrote "16)". Flagging the choice here.

Sources cross-checked while writing (all read this session):
- akar record codex-review-2026-09-14 (22 findings: 9H/11M/2L; triage list;
  fix-first list H1/H4/H6 -> s17 scope; external review = standing source)
- harvest records s17-s27 (outcomes, ships, implies lines, suite 84 -> 133)
- audit records 13-16 ("candidates: none"; 15 and 16 carry the corpus row)
- DESIGN.md sections 13-15 season tables through s27

Honesty deltas vs the brief (kept in the section):
- "9H/11M/2L landed across s17-s24": the record supports 21 of 22. Landed:
  H1-H9 (s18-s20), M1-M11 (s21-s23, M10 candidate closed s24), L2 (s21).
  L1 (discovery links vs generated filenames) has no harvest claiming it;
  checked against main on 2026-09-15, the discovery renderer still derives
  page hrefs from the raw record id while filenames use the slugified id
  (report.py, render_discoveries). Section 16 states exactly this.
- "the two workspace-rule violations": recorded in s21 - both writers edited
  the repository tree directly. Written as "the arc's two workspace-rule
  violations recorded here (both writers...)".
- zero-candidate audits: audit-13 and audit-14 named by s26's entry; audit-15
  and audit-16 also zero, with corpus rows. Section 16 states both facts.

## Deliverable 2 - README claim verification

w1's workspace copy (rimba/s28/w1/README.md, landed 02:57) is the
verification target. Legend: verified = executed or artifact-read this
session; documented = help/code text confirms, not executed; record-based =
akar/DESIGN record confirms, not re-executed. Zero false claims found.

| claim (w1 README) | verified | evidence |
|---|---|---|
| requires Python >=3.10 and pyyaml | verified | pyproject: requires-python ">=3.10"; dependencies ["pyyaml>=6.0"] |
| uv pip install -e . installs rumpun command | verified | pyproject [project.scripts] rumpun = "rumpun.cli:main"; .venv/bin/rumpun executed all session |
| version 0.11.0 agrees across pyproject, __init__, --version | verified | all three read 0.11.0 |
| init scaffolds rumpun.yaml, musim/s1.yaml, _template.yaml, prompts/base/, akar/, rimba/ | verified | ran rumpun init in w2 scratch-verify; ls shows all six (scaffold also writes a README.md the list omits - omission, not falsehood) |
| models --write fills routes: | verified | ran in scratch; routes block filled (glm, claude, gpt-6-astra, ...) |
| models read-only without flags | verified | bare models exit 0; rumpun.yaml sha256 unchanged |
| --probe spends quota: one completion per claude route | documented | models --help: "send one tiny completion per claude route (spends quota)"; not executed (quota) |
| lint blocks while season fields empty; exits 1 on errors | verified | fresh scaffold lint: exit 1, "goal is empty", "metric is empty" |
| lint errors block season start | verified | season start on same file: exit 1, "lint errors block season start (P27 preflight)", no spawn |
| graph prints mermaid DAG | verified | "graph TD" output: execute -> results.jsonl -> evaluate |
| direct appends pending directive; --list prints pending first | verified | append + --list in scratch ("0 pending verify direct claim"); --list help: "print all directives, pending first"; mixed-status ordering not exercised (single entry) |
| season start runs lint preflight; spawns benih one-shot; blocks until stop rule | verified preflight; spawn documented | executed preflight refusal (see above); spawn path read at engine.py:614-701; no live season run (quota) |
| season stop stops early; exit follows status mapping | documented | season stop --help + status_exit_code (engine.py:864-876); not executed (no running season) |
| harvest verdict choices WIN/LOSS/NEUTRAL/INVALID; --implies; --band/--observed verbatim | verified | harvest --help: choices + "recorded verbatim in the verdict row" |
| second harvest of same season refused | record-based | M3 landed s21 (DESIGN s21 entry; s21-harvest: "single verdict writer"); not re-executed |
| audit --last N default 10; appends one record; prints candidates | verified | audit --help default 10; ledger holds 16 audit records, audit-13..16 all "candidates: none" |
| a record carries at most 3 candidates | verified | MAX_CANDIDATES = 3 at audit.py:48 (also audit.py:571-572 slice) |
| board same view as season status; only season status takes --json | verified | diff of board s27 vs season status s27: identical; board --help has no --json; status --json printed machine form |
| season list prints "no state" when state absent | verified | "s1  no state" row in real repo |
| season show: status, deliverables, lane event counts | verified | s27 show: status line, per-agent file lists, "lane-build.jsonl 2 events" |
| deliverables exclude engine bookkeeping files | verified with nuance | BOOKKEEPING frozenset (agent.log, exit, prompt.md, prompt-meta.yaml, state.json, terminated, terminated.tmp, __pycache__) excluded at cli.py:254; nuance: agent-side .omc/ state files are not in the set and do appear in s27 show output |
| season report writes .rumpun/rimba/sN/report.html from persisted state | verified | rimba/s27/report.html exists, title "rumpun season s27 report"; render_index reads persisted state only, "Never mutates anything" (report.py:478-516) |
| --serve serves rimba/ read-only on http://localhost:8611 until Ctrl-C (exit 0) | documented | season report --help: "serve rimba/ over HTTP at http://localhost:8611"; port verified; Ctrl-C exit-0 not executed |
| evolve plan drafts sN+1 with empty primary_change skeleton | verified | plan wrote s2.yaml from s1 with empty primary_change |
| evolve apply runs the lint gate; fails until filled | verified | apply on empty draft: exit 1, per-field required errors |
| evolve approve records approval in akar; draft unmodified | verified | approve-s2.md record written; draft sha256 unchanged |
| evolve reject moves draft to musim/rejected/; records on_reject policy | verified | reject s3: draft moved to musim/rejected/s3.yaml; record: "P33 on_reject policy: action rollback_to_last_good; pause true; escalate_after consecutive_rejects 2" |
| evolve rollback moves season YAML to musim/rejected/; never runs git | verified with nuance | ran on s2: moved + rollback-s2.md record; evolve.py has no git/subprocess call ("this verb never runs git", evolve.py:330-332); nuance: succeeded on an approved-but-never-applied season, so "contains an applied season" states intent, not an enforced precondition |
| methodology changes cite akar evidence; lint refuses unresolvable citations | verified | bogus citation in methodology.evidence: exit 1, "evidence citation does not resolve in akar/"; digest check lint.py:147-177 (H7) |
| budget-cap finding never proposes a mutation | verified | audit-13..16 F6 lines: "campaign_cost_cap unset... operator sets the number; the tool only flags" |
| replay_corpus.py discovers evidence scripts, runs 6-script repro corpus vs current src, per-script isolation, writes replay-matrix.md | verified | tools/replay_corpus.py exists; matrix header: discovery path, "6 PASS, 0 FAIL, 0 DRIFT"; 6 PASS rows named (s18/w1-h6-loop, s18/w1-warn-repro, s19/w1-repro-h2-h3, s20/w1-repro, s22/w1-repro-m1, s22/w1-repro-m5) |
| verdicts PASS/FAIL/DRIFT/SKIP + UNCLASSIFIED row for unmatched | verified | matrix header defines all four; UNCLASSIFIED at replay_corpus.py:56 and 220-221 |
| audit reads newest matrix since s26; FAIL/REGRESSION arms candidate first | verified | audit-15/16 records: "corpus: 6 repro scripts green on main (no candidates)"; DESIGN s26 entry |
| render_dashboard.py renders index + discoveries + stateful seasons; skips stateless with logged reason; byte-identical re-runs | record-based, artifacts present | tool exists; rimba/index.html + s27/report.html on disk; determinism via s27 harvest + DESIGN s27 (two-pass rendering); not re-executed (writes outside w2 workspace) |
| --serve serves the same tree read-only on 8611 | documented | same help text as the --serve row above |
| everything except rimba/ is committed | verified | git ls-files .rumpun/: akar, musim, prompts, README.md, rumpun.yaml tracked; git check-ignore .rumpun/rimba/ confirms ignored |
| akar holds harvest, audit, approval, and rollback records | verified with nuance | real ledger: 27 harvest + 16 audit records; approval/rollback record types exercised in scratch (approve-s2.md, reject-s3.md, rollback-s2.md); production ledger holds none of those three types yet |
| relative paths in season YAML resolve against .rumpun/ | verified | engine.py:614 and 701 join benih["prompt"] to root |
| seeded pipeline is two phases; extra phases declarable | verified | graph output execute -> evaluate; musim/_template.yaml present for the non-seed shape |
| fight/collab semantics; lane rows are leads, not facts | design-record | DESIGN section 8; lane events visible in s27 show |
| season ends on all-exit / stall past stall_minutes / budget / operator stop | verified via ledger + mapping | ledger holds completed, stopped_stall (s4, s20), stopped_budget (s17); mapping covers stopped_operator |
| stall progress is appended log bytes; touch-only provides none; no history keeps mtime estimate | verified | engine.py:385-400 docstring (s24, closes M10) |
| exit mapping: completed/stopped_operator/running -> 0; failed/stopped_stall/stopped_budget -> 1 | verified | status_exit_code docstring engine.py:864-876 (unknown statuses also 1); executed: start preflight exit 1 |
| report pages carry provenance labels [H]/[A]/[D] | verified | s27 report.html: [H] x8, [D] x2; [A] in renderer code and discovery pages |
| git history over .rumpun/ is the evolution ledger; harvests become cited evidence | design-record + ledger | 43 sha256-stamped akar records; season YAML methodology.evidence citation fields |
| engine code stays fixed during a campaign; only YAML evolves | design-record | s21 workspace rule; DESIGN P37 |

Totals: 41 claims checked. 31 verified by execution or artifact read, 5
documented (help/code text, not executed: probe, live season spawn+block,
season stop live, --serve Ctrl-C, --serve repeat), 2 record-based (second-
harvest refusal, render determinism), 3 verified-with-nuance (show .omc
clutter, rollback precondition, akar approval/rollback record types).
Zero false claims. w1's band holds.

Scratch used for behavior checks: rimba/s28/w2/scratch-verify/ (own init,
models, lint, graph, direct, season start preflight, evolve
plan/apply/approve/reject/rollback, citation refusal). Nothing outside the
w2 workspace was written except this workspace's own files.
