# GLOSSARY — the rumpun component vocabulary

Ratified 2026-09-15, the s45 English rename (operator confirmation in
akar/directives.jsonl seq 3). The component vocabulary is English; rumpun
stays as the product name. Old names keep resolving as read aliases for
the historical seasons' yamls; new seasons and new scaffolds use the new
names.

| old | new | what it means |
|------|------|---------------|
| `benih` | `writers` | the season's agent roster: one entry per writer carrying name, route, lane, prompt, knowledge, and budget |
| `musim/` | `seasons/` | one YAML per season under `.rumpun/`; s1 is the seed |
| `akar/` | `ledger/` | the append-only evidence-record directory under `.rumpun/` (committed; git history over it is the evolution ledger) |
| `rimba/` | `runs/` | per-season agent workspaces under `.rumpun/` (gitignored) |
| `akar:` | `ledger:` | evidence-citation prefix naming a record as `<record-id>@<sha256>`; `akar:` still resolves, `ledger:` is preferred |

Citations resolve against the exact declared record and a matching body
digest: the full 64 hex chars or a unique prefix of at least 8.
