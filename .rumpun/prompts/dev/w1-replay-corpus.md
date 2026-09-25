# s25 w1 — the cross-season repro corpus runner

You are w1 in season s25 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/engine.py, and akar record audit-13
(zero candidates: the backlog is empty; this season closes the
cross-season verification gap). FILE TOOLS directly. WRITE ONLY inside
your workspace. 40 minutes.

## Deliverable: tools/replay_corpus.py (workspace copy) + the matrix

Discover every repro script under .rumpun/akar/evidence/*/ (known:
s18 w1-h6-loop.py + w1-warn-repro.py, s19 w1-repro-h2-h3.py, s20
w1-repro.py [evidence name] = repro_h5_h9.py, s22 w1-repro-m1.py +
w1-repro-m5.py, s23 w1-m2/w1-m8 are OUTPUT records not scripts - skip
non-scripts). For each:
- run it against the CURRENT repo src (most take a <src-dir> argument;
  some need PYTHONPATH=src; normalize per script with a small adapter
  table in the runner, documented);
- capture verdict: PASS (script exits 0 / prints its all-pass line),
  FAIL (exit nonzero or a failing line), DRIFT (the script's hardcoded
  assumptions no longer hold on main - e.g. paths, fixtures, landed
  features changing expected output - record what moved);
- emit a markdown matrix: script | verdict | first failing line | note.

Runner rules: physical file, stdlib, logging, subprocess isolation per
script (timeout per script, cleanup in finally), never print script
stderr content beyond the verdict lines, and the matrix lands in your
workspace as replay-matrix.md for the harness to commit under evidence.

## Constraints

- ruff clean; py3.10+; no new dependencies.
- Do not modify src/ or tests/ - w2 owns fixes; you own the runner.
- A FAIL you can fix by ADAPTING THE RUNNER (not the script's meaning)
  is runner work; a FAIL that reveals a real regression on main is
  w2's - record it clearly in the matrix as REGRESSION.

## Verify before finishing

Run the runner: matrix emitted, every discoverable script accounted
for (including honest SKIP with reason for scripts that cannot run
headlessly). Runner + matrix + notes.md in your workspace.
