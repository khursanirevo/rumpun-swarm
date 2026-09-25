# akar record: codex-bwrap-sandbox

id: codex-bwrap-sandbox
date: 2026-09-14
source: rumpun codex critique session 2 (proposals/codex-2026-09-14-s2.md)
verdict: NEUTRAL (tool defect, workaround recorded)

codex-cli 0.154.0 with --sandbox read-only failed every file read this machine:
`bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`. The critique ran
on the session brief instead of DESIGN.md's literal text.

Implications:
- Critique sessions that need repo grounding must inline the design text in the
  prompt on this machine until the sandbox defect is fixed.
- GitHub issue draft owed (codex is OpenAI's repo; draft under
  khursani8/khursanirevo per operator rule 4, then hand over).
