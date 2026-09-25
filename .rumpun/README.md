# rumpun project

Bootstrap a self-evolving multi-agent swarm. Design: DESIGN.md (repo root of the rumpun CLI).

## Layout
- `rumpun.yaml` — campaign config: goal, autonomy stages, budget cap, routes.
- `musim/` — one YAML per season. s1 is the seed; fill goal/metric, then lint.
- `benih/` — seed agent definitions (per-project overrides).
- `akar/` — append-only shared memory: harvest findings, evolution records, directives.
- `rimba/` — per-season workspaces (gitignored).
- `prompts/base/` — phase prompt templates; season overrides go in `prompts/s<N>/`.

## First season
1. Fill `campaign.goal` and `campaign.metric` in rumpun.yaml.
2. Fill `goal`/`metric` in musim/s1.yaml.
3. `rumpun lint musim/s1.yaml` — must pass before anything spawns.
4. `rumpun graph musim/s1.yaml` — eyeball the DAG.
5. `rumpun models` — probe spawnable routes (not yet implemented, build order step 2).
6. `rumpun season start` — run the season (not yet implemented, build order step 3).
