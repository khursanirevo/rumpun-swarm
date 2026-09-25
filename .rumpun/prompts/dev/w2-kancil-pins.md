# s67 w2 — spec-first pins for the kancil route and the scaffold

You are w2 in season s67 (repo root: /mnt/data/work/rumpun; kancil lives
at /mnt/data/work/kancil). Read rumpun.yaml's routes map, src/rumpun/
scaffold.py, and ledger records s66-harvest + audit-42 + directives
seq 2/9/10; the s66 pins (tests/test_s66_w2_pins.py) are the shape
precedent. You own tests/; w1 owns rumpun.yaml + scaffold. FILE TOOLS
directly. WRITE ONLY inside your workspace. 40 minutes.

## Spec-first pins (red against current code)

1. The kancil route spawns: a stub kancil on PATH (a script echoing the
   prompt to a file) driven through a season start renders the prompt
   into the stub's file and the season completes - the route is real,
   not a config line (subprocess, 240s bound).
2. The kaggle-base pack installs into a fresh scaffolded campaign:
   distill emits the draft, install lands it digest-verified, plugin
   list shows it (subprocess, 240s bound).
3. The competition template lints clean and names the fill-in fields
   (competition, metric, band).

## Constraints
- tests/ additions-only; subprocess pins, timeout bounded (240s).
- logging, never print; ruff clean (line-length 100); py3.10+.
- Do not modify src/ or tools/ - w1 owns rumpun.yaml + scaffold; the
  harness merges.

## Verify before finishing
Measured red set in notes.md; the pins green at merge; the suite floor
holds.
