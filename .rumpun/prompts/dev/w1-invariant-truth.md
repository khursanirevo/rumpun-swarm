# s34 w1 — falsify_required enforcement in lint

You are w1 in season s34 (repo root: the parent of this .rumpun tree). Read
src/rumpun/lint.py, the campaign rumpun.yaml (autonomy.invariants), and akar
records audit-23 + usefulness-decade-3. FILE TOOLS directly. WRITE ONLY
inside your workspace. 40 minutes.

## Deliverable: lint enforces the falsify_required invariant

Today: rumpun.yaml declares falsify_required, but nothing checks it — the
s12 lean trim removed the falsify phase and no lint rule noticed. Fix:
when a season's autonomy declares falsify_required (read the campaign
rumpun.yaml), the season yaml must carry an evaluate-phase (or any phase)
whose `reads` names an artifact — a season that could never disconfirm
its verdict fails lint with an error naming the season. Enforcement
reads the CAMPAIGN config (root/rumpun.yaml autonomy.invariants), so
campaigns without the invariant are unaffected.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not touch audit.py, collab.py, harvest.py, evolve.py, cli.py,
  report.py, tests/ (w2 owns the pins; the harness merges).
- The existing seasons' yamls (all carry execute reading nothing? check:
  the lean pipeline's evaluate reads results.jsonl) — verify every
  musim/*.yaml still lints; the enforcement targets seasons with NO
  reading phase at all.

## Verify before finishing

Repros: a season declaring falsify_required with zero reading phases
fails lint (error names it); the current lean pipeline passes; a
campaign without the invariant passes untouched. Suite green against
patched copies. All in notes.md.
