# akar record: agentlog-no-tool-evidence
id: agentlog-no-tool-evidence
date: 2026-09-14
title: log text carries no tool evidence
finding: agent.log text streams carry NO deterministic tool-invocation evidence

calibration over all 31 recorded rimba agent.logs (s2-s14, script + output in
akar/evidence/s14/): rule "bytes >= 512 AND no tool marker" gives
tp=7 fn=1 fp=21 tn=2.

- under-detect: s14/w1 is tool-less yet its log contains tool_use,
  tool_result, function_call markers (its ToolSearch + MCP state-tool
  transcripts are IN the stream). Marker families H1 and H2 both break.
- over-detect: clean logs carry zero markers (the claude CLI text output
  never records tool events), so "no markers" matches every clean spawn.
- size does not separate either: tool-less logs span 1.4k-24.2k bytes,
  clean logs 1.6k-2.7k, ranges overlap.

implies: audit-2's "add spawn tool-check" candidate is unsatisfiable on log
TEXT. The deterministic path is structured spawn output: rewire routes to
claude -p --output-format stream-json and classify tool evidence from parsed
events. That rewire is s15's cited candidate.

update: tool-less spawns now 8 of 26 (s14/w1); supersedes the count in
glm-toolless-spawn. Related: glm-toolless-diagnostic, audit-2.

sha256: 6354b9374c65d0f553ce5610f0e68c33e7c98f4277459e8876deee2fcbb0fe92
