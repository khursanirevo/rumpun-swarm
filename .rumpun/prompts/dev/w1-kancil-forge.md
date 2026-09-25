# s68 w1 — the kancil forge flow (directive seq 13)

rumpun improves kancil through GitHub: propose from usage evidence, file
the issue, land the PR, merge, then update the pip-installed kancil.

## Ground truth (measured 2026-09-16)
- remote: github.com/khursanirevo/exp_manager (kancil's repo)
- gh CLI authed as khursanirevo; kancil 2.2.4 installed at
  ~/.local/bin/kancil; source at /mnt/data/work/kancil
- the s67 route: `kancil loop --prompt {prompt} --iteration-timeout 1800`
  (rumpun.yaml routes); w2's pins prove the spawn

## Task
1. Check `git -C /mnt/data/work/kancil status` first; branch from main.
2. Read the campaign ledger + runs/s67 logs for REAL usage friction with
   kancil as a rumpun writer route (loop semantics, stop sentinel,
   iteration-timeout, prompt file contract). Propose ONE evidence-cited
   improvement. No invented friction.
3. `gh issue create -R khursanirevo/exp_manager` — title + body cite the
   evidence (ledger record ids with shas).
4. Implement in /mnt/data/work/kancil on a branch; kancil's own tests
   must pass; push; `gh pr create -R khursanirevo/exp_manager`.
5. Merge the PR (the operator's directive authorizes merge), then update
   the installed kancil: `uv tool install /mnt/data/work/kancil --force`
   or `uv pip install /mnt/data/work/kancil` matching how 2.2.4 was
   installed. Record which.
6. Re-run tests/test_s67_w2_pins.py solo to prove the route still spawns
   against the updated CLI. Write notes.md with issue/PR numbers.

## Bounds
- One issue, one PR. No force-push. If kancil's tests fail, stop and
  record the state instead of merging.
- Never touch rumpun source; never modify .rumpun state.
