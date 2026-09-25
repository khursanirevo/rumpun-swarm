# s38 w1 — the checker verifies the loop LOOPING

You are w1 in season s38 (repo root: the parent of this .rumpun tree). Read
tools/coldstart_check.py (your s37 checker), README.md (the documented
lifecycle), and akar records audit-27 + usefulness-decade-3. FILE TOOLS
directly. WRITE ONLY inside your workspace. 40 minutes.

## Deliverable: the propagation steps added to tools/coldstart_check.py
(workspace copy)

After the s37 lifecycle (through harvest + audit), the checker continues:
7. rumpun audit has landed audit-1 (verify the record exists).
8. rumpun evolve plan drafts musim/s2.yaml (the audit's reflection seeds
   the next season - the loop's defining step).
9. The drafted s2 is minimally edited (stub model route + benih, same as
   s1's edit) and rumpun lint passes on it.
10. rumpun season start runs s2 to completed against the stub model.
11. rumpun harvest marks s2's verdict.
Each step PASS/FAIL-logged with its command; exit nonzero on the first
failure; the step count in the summary updates. The temp dir survives
(printed at the end). No campaign state touched.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not modify src/, tests/, or any file outside your workspace.
- The 178-test suite stays green.

## Verify before finishing

Run the extended checker: every step PASS through s2's harvest, exit 0,
temp dir printed with musim/s2.yaml + s2 artifacts in place. Suite green
(178). Both in notes.md.
