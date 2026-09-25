# s44 w2 — spec-first pins for the plugin boundary + the kaggle-base seed

You are w2 in season s44 (repo root: the parent of this .rumpun tree). Read
the operator's plugin/hub directive (the direct ledger), akar record
audit-33, and DESIGN.md section 16 (the arc whose proven gates become the
seed priors). You own tests/ + the kaggle-base seed draft; w1 owns
plugin.py + cli wiring. FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Deliverables

1. Pins (tests/ additions-only, red against current code):
   - a valid minimal pack passes plugin lint
   - a sid in priors/ fails naming file and line
   - an absolute path in priors/ fails
   - a private-vocabulary match fails
   - the installer's discovery sees priors/ only: a campaign/ dir with
     sids and secrets is invisible to it
   - manifest violations (missing name/version/digest) fail
2. The kaggle-base seed draft (priors/ only, generalized from this
   campaign's proven gates - NO project sids or names):
   - patterns/the-falsify-gate.md: verdicts must face disconfirming
     evidence (from s34)
   - patterns/the-band-mask-guard.md: bands must define integration
     (from s32)
   - patterns/stall-resume.md: hung cycles resume at 1.5x budget
     (from s36)
   - seasons/a-season-template.yaml: the lean execute -> evaluate shape
   Each file ends with its generalization source noted as a pattern,
   not a project reference.

## Constraints

- tests additions-only vs the current repo file (188 tests kept).
- The seed draft lives in your workspace under seed/kaggle-base/ and is
  PROSE-REVIEWED by you before landing: it must read as general knowledge.
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ — w1 owns plugin.py + cli wiring.

## Verify before finishing

Measured red set against current code in notes.md; the 188 existing
tests green; the seed draft reads as general knowledge with zero project
references.
