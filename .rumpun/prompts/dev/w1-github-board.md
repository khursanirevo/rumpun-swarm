# s69 w1 — rumpun's GitHub home + Project board (directive seq 14)

The campaign repo has no git remote. Give rumpun a GitHub home and a
Project board so any instance can file work and any instance can pick
it up.

## Ground truth (measured 2026-09-16)
- gh CLI authed as khursanirevo (verified); kancil's forge flow (s68)
  proved the issue->PR->merge path on khursanirevo/exp_manager
- the campaign repo: /mnt/data/work/rumpun, branch main, no remote
- global rule: GitHub targets only khursani8/khursanirevo

## Task
1. `gh repo create khursanirevo/rumpun --private --source
   /mnt/data/work/rumpun --push` (private; the ledger pushes with it -
   that is the point: other instances resume from it). If the repo
   exists, add it as remote `origin` and push main instead.
2. `gh project create --title "rumpun" --owner khursanirevo` (a Projects
   v2 board). Record the project number/url.
3. Seed the board with ONE real issue from the campaign's open items:
   directive seq 0 (audit panel tooling) is the strongest candidate.
   `gh issue create -R khursanirevo/rumpun`, then `gh project item-add`.
4. Write a notes.md listing: repo url, project url/number, issue url,
   and the exact commands used. REQUIRED - s68 shipped no notes.

## Bounds
- Private repo. No force-push. No history rewrite.
- Never touch kancil's repo; never edit .rumpun state files.
