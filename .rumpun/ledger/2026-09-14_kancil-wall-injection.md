# akar record: kancil-wall-injection

id: kancil-wall-injection
date: 2026-09-14
source: kancil post-mortem, ratified into rumpun P35
verdict: LOSS (process), retained as design evidence

Three same-family agents re-derived an already-closed dead end even though the
closing evidence existed on disk. Storage was not the defect; injection was.
Nothing put the closed axis in front of the agents at spawn.

Implication for rumpun: dead-end knowledge must be injected into every agent at
spawn regardless of knowledge staging (P35 closed-wall registry), not merely
persisted in akar. Bounded injection per P36 session-2 amendments: recorded
wall ids, review dates, deterministic scope.
