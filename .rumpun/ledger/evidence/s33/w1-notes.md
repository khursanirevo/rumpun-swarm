# s33 w1 — the decadal usefulness audit (tools + audit trigger)

## Verdict first

Both deliverables landed and verified. Repros green, ruff clean, suite 150/150
against the patched src. Two honest caveats: the suite run through a tests COPY
in scratch fails one location-sensitive pin (artifact, see below); the 300s
route-timeout branch is not live-reproduced (it would burn 300s) and mirrors
refresh_corpus_matrix's pinned timeout pattern instead.

## What landed

1. tools/usefulness_audit.py (new; merge-ready copy at this workspace's tools/):
   - brief = season count from musim/ + per-season verdict history (last
     season-level row per rimba/<sid>/verdicts.jsonl) + DESIGN.md sections
     13-16 verbatim (from the "## 13." heading to EOF).
   - route: rumpun.yaml usefulness.route names a routes: key; default
     gpt-6-astra. Rendered exactly like the engine
     (template.replace("{prompt}", path)), spawned as /bin/sh -c in its own
     process group, stdin=/dev/null, streams captured, 300s hard timeout
     (killpg SIGKILL).
   - verdict: the last "VERDICT:" line, exact match against USEFUL /
     PARTIALLY USEFUL / SELF-LOOP DOING NOTHING; residuals: "residual:"
     lines, one line each, 200-char bound.
   - record usefulness-decade-<N> via akar.append_record (H6 lock, dedup):
     verdict, residual summaries, musim count, evidence pointer
     (akar/evidence/usefulness-decade-<N>/output.txt) + its sha256. Prompt
     and route output are never echoed into the record.
   - refuses honestly (exit 1, no record): missing config or route, call
     fail, timeout, no verdict token, nothing due, duplicate id.
   - decade N = first decade without a record (10 seasons per decade) — the
     audit gate's fixed point; debt is paid in order.
2. audit.py (patched copy at src/rumpun/audit.py; diff vs repo is 4 regions:
   docstring rule, 2 constants, _usefulness_decade_due helper, F7 call site
   after the F6 block):
   - fires "F7 usefulness decade: usefulness audit due for decade N
     (different-model review) — <count> musim seasons, <k> records" when
     floor(count/10) > number of usefulness-decade-* records.
   - N = first missing decade; the line is a finding only, never in the
     candidates list; akar.AkarError wraps into AuditError; no new line when
     the gate is closed (byte-compatible with audit-19/20 behavior).

## Verification (all ✅ measured this session; logs in results/)

| Check | Result |
|---|---|
| baseline suite (repo src, repo tests path) | 150 passed, 59.6s |
| patched suite (PYTHONPATH = this workspace's src) | 150 passed, 54.2s |
| suite via tests COPY under scratch/tests | 149 passed, 1 failed — artifact |
| repro_decade.py (resolution probe + C1-C5) | ALL CHECKS PASSED, exit 0 |
| repro_runner.py (B1-B3, A, Z) | ALL CHECKS PASSED, exit 0 |
| ruff --no-respect-gitignore (tool, patch, 2 repros) | clean |

Repro details:
- Decade finding: fires decade 1 at 10 seasons; NOT at 9 (patched lines and
  full appended record bodies byte-identical to the unpatched module); 20
  seasons + decade-1 record fires decade 2; + decade-2 goes silent; 30
  seasons + only a decade-9 record fires decade 1 (first missing, not
  current); candidate lines unchanged by the patch.
- Runner: the stub route writes usefulness-decade-1 with verdict USEFUL, the
  residual summary, and the evidence pointer/sha; the captured output proves
  fd0=/dev/null (stdin isolation, live); missing route, exit-3 route, silent
  route, and rerun-after-record each exit 1 with no record and the named
  reason; a failing route's captured streams still land under evidence for
  the operator.

Suite caveat (for w2 and the harness): the tests copy under scratch fails
test_replay_matrix_has_no_regressions because that pin derives the repo from
Path(__file__).parents[1] (tests/test_rumpun.py:3352), which resolves to the
workspace root from a scratch copy. The same test passes against patched src
from the repo path, and the full repo-path suite is 150/150 green with the
patched PYTHONPATH. No tests/ file was modified.

Reproduce (absolute paths; shell cwd resets between calls):

```
V=/mnt/data/work/rumpun/.venv/bin/python
W=/mnt/data/work/rumpun/.rumpun/rimba/s33/w1
$V $W/scratch/repro_decade.py
$V $W/scratch/repro_runner.py
PYTHONPATH=$W/src $V -m pytest /mnt/data/work/rumpun/tests/test_rumpun.py -q
/home/sani/.local/bin/ruff check --no-respect-gitignore \
  $W/tools/usefulness_audit.py $W/src/rumpun/audit.py $W/scratch/repro_decade.py \
  $W/scratch/repro_runner.py
```
