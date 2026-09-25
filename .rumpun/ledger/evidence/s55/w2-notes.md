# s55 w2 — spec-first pins for the artifact check: notes (2026-09-16)

Spec anchors: seasons/s54 ships row + the s55 w2 prompt (`.rumpun/prompts/dev/w2-check-pins.md`);
ledger records 2026-09-16_s54-harvest (s54 WIN, sha256 7340c8c3…) and 2026-09-16_audit-39
("Independent artifact checks remain absent here"); w1's prompt
(.rumpun/prompts/dev/w1-artifact-check.md) for the checker contract.
Precedent files: tools/replay_corpus.py (--repo/--out-dir flags, bounded subprocess),
tests/test_s53_w2_pins.py (git fixtures, bounded runs), s54 notes (this shape).

## Deliverable

tests/test_s55_w2_pins.py — 6 pins, additions-only, `_s55w2_` helpers,
py3.10+, ruff clean at line-length 100, no prints. All 6 red pre-merge;
all red for the spec reason. The tampered scenarios build their own git
fixtures in tmp_path; no pin writes the real ledger or DESIGN.md.

## Interface contract the pins hold (for w1)

- Call: `python tools/artifact_check.py <sid> <close-commit> [--repo ROOT] [--out-dir DIR]`
  (--repo/--out-dir follow the tools/replay_corpus.py flag precedent).
- --out-dir receives the check-<sid> record, created when missing;
  default <repo>/.rumpun/ledger. Every pin redirects it into tmp_path.
- The record carries `id: check-<sid>` and the verdict token VERIFIED
  (honest, exit 0) or DELTA (detected tamper, exit 1); refusals exit
  nonzero and name what is missing (the sha, the sid, the pins file).
- Honest record cites its commands (pytest on the season's pins file, the
  git archive extraction, a digest section) and shows a "N passed" pins
  outcome with no failed count.

## Measured red set (solo, pre-merge, current main 614aabf)

Two snapshots, because w1 landed and then rewrote the tool mid-measurement:

Snapshot A — tools/artifact_check.py present but corrupted (mtime
2026-09-16 10:17:24, 336 lines, dies at import): SyntaxError line 106
(`PINS_CLAIM_RE = re.compile(r\b(\d+) pins\b)` — unquoted raw string);
a second latent defect sits below it (module-level `re.finditer` bound to
KEY_TOKEN_RE, referencing an undefined name). Command: PYTHONPATH=src
.venv/bin/python -m pytest tests/test_s55_w2_pins.py -q. Result:
**6 failed in 0.46s**. Every red is for the spec reason.

| pin | clause | outcome | measured reason (snapshot A) |
|---|---|---|---|
| 1 honest close | spec 1 | RED | rc 1 (import crash), expected 0 |
| 2 ships tamper | spec 2 | RED | rc==1 passed coincidentally (crash also exits 1), then no record: out dir never written |
| 3 digest tamper | spec 2 | RED | same shape as pin 2 |
| 4 missing commit | spec 3 | RED | crash traceback names no sha |
| 5 unknown sid | spec 3 | RED | crash traceback names no sid |
| 6 pins collect failure | spec 3 | RED | crash traceback names no pins file |

Snapshot B (current) — the tool is absent: w1 deleted it for a clean
rewrite (their stream says so). Re-run: **6 failed in 0.33s**, each at
launch: "can't open file …/tools/artifact_check.py: [Errno 2]".

## Honest-close feasibility (measured)

The s54 pins pass inside the extracted close commit: git archive 614aabf
-> /tmp/s55w2_extract, PYTHONPATH=<tree>/src, repo venv: **8 passed in
6.60s, exit 0** (/tmp/s55w2_honest_probe.log). Precondition for pin 1
going green at merge holds.

## Merge gates (measured)

- Full suite with the pins file added: **7 failed, 242 passed in 109.77s**
  (/tmp/s55w2_full.log, exit 1). The 7th red is the s38 coldstart pin,
  red for an environmental reason, not a code change: its before/after
  snapshot of the repo .rumpun tree differs only in the four LIVE session
  files (.rumpun/runs/s55/w1/{agent.log,state.json} and
  .rumpun/runs/s55/w2/{agent.log,state.json}) — season-writer log appends
  during the 44s run. Mid-season, any live lane reds that pin.
  Expected green at merge on a quiet tree.
- Floor: 242 of the 243 pre-existing pins green; the one red is the s38
  snapshot race above. At merge: 243 + 6 = 249 green, zero reds.
- ruff: `~/.local/bin/ruff check --no-respect-gitignore --line-length 100`
  on the pins file → All checks passed (one E501 fixed pre-measurement).
- Interpreter: repo .venv python 3.13.12, pytest 9.1.1, PYTHONPATH=src.

## Logs (all outside the repo)

/tmp/s55w2_solo.log (snapshot A), /tmp/s55w2_solo2.log (snapshot B),
/tmp/s55w2_full.log (full suite), /tmp/s55w2_s38_solo.log (s38 evidence),
/tmp/s55w2_honest_probe.log (extracted-tree pins run).
