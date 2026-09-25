# s21 w1 — M3 unified verdict source + M11 route generator fix

You are w1 in season s21 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/harvest.py, src/rumpun/routes.py,
src/rumpun/scaffold.py, and akar record codex-review-2026-09-14 (M3 + M11).
FILE TOOLS directly; no nested-heredoc scripts. 40 minutes.

## M3 — harvest becomes the single verdict writer

Today: harvest_season writes ONLY the akar record; report and audit read
rimba/<sid>/verdicts.jsonl — which the harness has maintained BY HAND at
every close (two books, M3). Fix: harvest_season ALSO appends the
season-level verdict row to rimba/<sid>/verdicts.jsonl, exact shape of the
existing rows: {"season": sid, "verdict": ..., "metric": ..., "band": ...,
"observed": ..., "implies": ...} — band/observed defaulting from what the
caller passes (extend harvest_season's signature with optional
band/observed args, defaulting empty; the CLI --implies maps to implies).
Refuse a second harvest of a terminal season already carrying a season row
(M4's guidance, minimal form). Report and audit stay unchanged — they
already read this file.

## M11 — routes.py stops generating placeholders

Today routes.py's write_routes emits `--model <model>` literally (the
defect fixed ad hoc in the campaign copy at s15; the generator kept
generating it). Fix: generate a CONCRETE default model per family (claude
family: the operator's current fable id is fine as a documented default;
gpt family: the reviewed codex bypass route) and validate each generated
command with /bin/sh -n before writing (raise on non-zero). Scaffold
emits what routes.py generates — one mechanism, no copy.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch lint.py, akar.py, evolve.py, engine.py, cli.py, tests/
  (w2 owns the test pins; the harness merges).
- Existing report/audit behavior unchanged (they read verdicts.jsonl
  already); the 99-test suite stays green.

## Verify before finishing

Repros: harvest a scratch WIN season then render — the page's verdict is
WIN with no hand-written verdicts.jsonl; second harvest refuses. Run
/bin/sh -n over every command write_routes generates. Suite green against
patched copies. All in notes.md.
