# akar record: panel-s83-error
id: panel-s83-error
date: 2026-09-17
title: panel route error s83 (pending)
status: pending
route: gpt-6-astra (bounded 300s)
error:
gpt-6-astra route exited 1: Reading additional input from stdin... OpenAI Codex v0.154.0 -------- workdir: /mnt/data/work/rumpun model: gpt-6-astra provider: openai approval: never sandbox: danger-full-access reasoning effort: medium reasoning summaries: none session id: 01a0aef7-0785-7bf2-acad-45031ebca191 -------- user /mnt/data/tmp/panel-prompt-56491ugu.md 2026-09-17T10:43:40.466950Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when Deserialize(Error("data did not match any variant of untagged enum JsonRpcMessage", line: 0, column: 0)) 2026-09-17T10:43:40.485545Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when Deserialize(Error("data did not match any variant of untagged enum JsonRpcMessage", line: 0, column: 0)) 2026-09-17T10:43:40.492185Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when Deserialize(Error("data did not match any variant of untagged enum JsonRpcMessage", line: 0, column: 0)) hook: SessionStart hook: SessionStart Completed hook: UserPromptSubmit hook: UserPromptSubmit Completed ERROR: Your workspace is out of credits. Ask your workspace owner to refill in order to continue. ERROR: Your workspace is out of credits. Ask your workspace owner to refill in order to continue.
sha256: 2fea8a5c8ec8061b62f777d9202128b68b060eccf916fee679564b1856b728f3
