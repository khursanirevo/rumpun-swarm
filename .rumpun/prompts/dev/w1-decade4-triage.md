# s42 w1 — decade-4 usefulness audit: run + residual triage

You are w1 in season s42 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-16, tools/usefulness_audit.py, and akar records
audit-31 + codex-usefulness-2026-09-15. FILE TOOLS directly. WRITE ONLY
inside your workspace. 40 minutes.

## Deliverable 1: run the decade-4 usefulness audit

Execute: .venv/bin/python tools/usefulness_audit.py
(from the repo root; the route is rumpun.yaml's gpt-6-astra bypass —
this calls the real different-model auditor against the full ledger).
The runner lands usefulness-decade-4 with the verdict, residuals, and an
evidence pointer. It refuses honestly if anything fails — surface that,
do not retry blind.

## Deliverable 2: residual triage (notes.md)

For EVERY residual in usefulness-decade-4: confirmed or refuted against
source, with the file:line or record that decides it. The prior decade's
residuals (usefulness-decade-3): which were closed by which season, which
remain open — a closing ledger for the decadal findings.

## Constraints

- Never echo the route's raw output into notes.md beyond the verdict and
  residual lines; never token values.
- Do not modify src/, tests/, tools/, or files outside your workspace.
- The 171-test suite stays green (this season changes no code).

## Verify before finishing

The usefulness-decade-4 record exists with a parsed verdict; your triage
covers every residual. Both in notes.md.
