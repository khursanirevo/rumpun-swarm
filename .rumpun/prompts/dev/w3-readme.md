# Task: write README.md (the first repo README)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s3/w3. Write ONLY README.md,
notes.md into this workspace. Do not touch anything outside it.

rumpun: a CLI that bootstraps a self-evolving multi-agent swarm in a folder,
configured from YAML, with git history as the evolution ledger. All project
state lives in .rumpun/ (committed; only .rumpun/rimba/ is gitignored).

First read src/rumpun/scaffold.py and .rumpun/README.md so the quickstart
matches what init actually scaffolds. If init does not seed a season yaml,
show creating .rumpun/musim/s1.yaml in the quickstart.

Sections:
1. What it is — three sentences, no marketing words.
2. Install — uv pip install -e . from a clone.
3. Quickstart — exact commands in order, one line under each saying what it
   does. The full implemented verb surface of rumpun v0.3.0 is exactly:
     init [TARGET]
     lint FILE
     graph FILE
     models [--write] [--probe]
     board ID
     harvest ID --verdict {WIN,LOSS,NEUTRAL,INVALID} --implies TEXT
     season start FILE [--json]
     season status ID [--json]
     season stop ID
     season report ID
     evolve plan FILE
     evolve apply FILE
   Do NOT invent flags or verbs. season list/show/direct and evolve
   approve/reject/rollback exist as named stubs that exit 2 — list them
   under an honest "Not implemented yet" heading.
4. The .rumpun/ directory — table: rumpun.yaml (campaign config), musim/
   (one YAML per season), prompts/ (task templates), akar/ (evidence ledger,
   committed), rimba/ (season workspaces, gitignored).
5. Season lifecycle — fight vs collab in two sentences; the four stop rules
   in one line.
6. Design pointer — DESIGN.md is the canonical record; seasons cite akar
   records as evidence.

Rules: every command shown must be runnable as written; no emoji; no
marketing adjectives. notes.md: what you checked to make the commands real.
