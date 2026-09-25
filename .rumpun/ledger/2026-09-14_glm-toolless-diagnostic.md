# akar record: glm-toolless-diagnostic
id: glm-toolless-diagnostic
date: 2026-09-14
title: one stripped-env spawn came up healthy; causality unproven
Diagnostic after the engine env-strip patch: one glm-route spawn
(cat prompt | claude -p --dangerously-skip-permissions) with ANTHROPIC_MODEL
and ANTHROPIC_DEFAULT_*_MODEL removed wrote /tmp/rumpun-diag/hello.txt
containing OK and replied DONE: full file-tool set present. Its log still
shows model glm-5.2[1m] (relay default), so the suffix was not removed and
the strip is not the proven lever. Conclusion for the ledger: the tool-less
condition is intermittent (4 of 16 spawns), the strip is a harmless shipped
mitigation, and causality is unproven in both directions. Operational rule
stands: detect the blocker at harvest, retry the missed deliverable next
season, harness-build if it repeats (s1 precedent).
sha256: 67da0f301008aa3ff4edaaca0e17a4655947d275e5b179c5efce439227fb0298
