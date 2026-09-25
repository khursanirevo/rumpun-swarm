# s49 w1 — the corpus runner's superseded-repro skip

You are w1 in season s49 (repo root: the parent of this .rumpun tree). Read
tools/replay_corpus.py (the runner + the adapter table), and akar records
audit-37 + s48-harvest (the s48 re-seal: the s22 archived repro's contract
replaced by the M5 behavior, verified 23/23 GREEN — the archived repro is
superseded, not broken). FILE TOOLS directly. WRITE ONLY inside your
workspace. 40 minutes.

## Deliverable: the adapter table's superseded entry

The runner's adapter table gains one entry: the s22 archived repro
(repro_m5_failed_exit) is SUPERSEDED by the s48 re-sealed repro (at
evidence/s48/w1-repro.py). The runner skips it with the reason recorded
in the matrix (a SKIP row: "superseded by the s48 re-seal at
evidence/s48/w1-repro.py"). The DRIFT row for that script retires from
the audit's candidates (the skip removes the script from the FAIL
classification).

## Constraints

- The adapter table's skip is one entry; the runner's discovery,
  execution, and matrix emission are unchanged for the other scripts.
- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not modify tests/ or files outside your workspace.
- The 188-test suite stays green.

## Verify before finishing

Repro: the runner's matrix carries the SKIP row citing the supersession;
the other five scripts still run and pass. Suite green. Both in notes.md.
