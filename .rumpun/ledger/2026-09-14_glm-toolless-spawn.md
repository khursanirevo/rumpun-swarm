# akar record: glm-toolless-spawn
id: glm-toolless-spawn
date: 2026-09-14
title: glm route spawned a claude session with no file/exec tools
Season s4 w1 (route glm: cat prompt | claude -p --dangerously-skip-permissions)
booted with only ToolSearch, locked python_repl, and ast-grep: no Read, Write,
Edit, Bash, Grep, or Glob. python_repl refused open() (GyoshuSecurityError).
The agent wrote nothing and could not post lane events; w2 then starved
waiting for w1's policy event; the season hit the 15-minute stall rule.
Same route produced full artifacts in s2 (4/4) and s3 (3/3), so the failure
is intermittent, not config-deterministic. Log: env warning about
ANTHROPIC_API_KEY overriding claude.ai login; model resolved as glm-5.2[1m].

GitHub issue draft (owner khursani8, hand over; not filed by harness):
  Title: claude -p sessions intermittently start with no core file/exec tools
  Body: Running claude -p --dangerously-skip-permissions (v-series CLI behind
  an anthropic-compatible relay), a session may come up with a partial
  toolset: no Read/Write/Edit/Bash/Grep/Glob; a sandboxed python_repl blocks
  open(); the model then reports "blocked, no tools" instead of failing at
  startup. Expected: detect the tool inventory at session start and fail
  loudly (non-zero exit) when core file tools are absent, or emit a startup
  warning. Repro: intermittent; 1 in 8 identical spawns in our seasons.
  Workaround: operator inspects agent.log for the blocker pattern and
  re-runs the benih.
sha256: dbfd74ccd9bd076e3a1de5c0afd244cd461f2ffcfb794dda98764a0a7bf257f9
