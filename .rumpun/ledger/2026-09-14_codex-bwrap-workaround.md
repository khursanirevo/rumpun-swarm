# akar record: codex-bwrap-workaround
id: codex-bwrap-workaround
date: 2026-09-14
title: bypass-sandbox restores codex file access; gpt routes viable
Follow-up to codex-bwrap-sandbox: a route probe (codex exec
--dangerously-bypass-approvals-and-sandbox -m gpt-6-astra, codex-cli 0.154.0)
read /mnt/data/work/rumpun/README.md via head and returned the correct first
line (# rumpun), 4026 tokens, exit 0. The read failure is therefore scoped to
the sandboxed mode; bypass mode is a working workaround. rumpun's route table
already uses bypass for all codex routes, so the gpt-* routes are viable
end-to-end. Residual noise: rmcp transport worker errors at session start
(JsonRpcMessage deserialize), harmless to the run. First full gpt-6-astra
review of the campaign launched 2026-09-14; findings route into the akar
ledger as reflection evidence.
sha256: 5ebecf8f2f15869af7d8b5c519818c9e488cbe87801edb6fd119633adefe4f80
