# Task: process-level dual-start test for the state lock (full test file into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s6/w2. Write ONLY
test_rumpun.py, notes.md, lane_tool.py into this workspace. Do not touch
anything outside it.

Base your test_rumpun.py on the CURRENT repo file
/mnt/data/work/rumpun/tests/test_rumpun.py (read it first; keep all 19
existing tests passing).

Add one integration test, no mocks, no skips:
  test_dual_start_single_spawner(tmp_path)
- Build a scratch project: <tmp>/proj/.rumpun with rumpun.yaml
  (autonomy stage manual, invariants [goal_immutable, budget_cap,
  falsify_required], routes: glm: "cat {prompt} > /dev/null"), a minimal
  valid season s1.yaml (fixture SEASON_S1 shape already in the file works),
  prompts/dev/dummy.md, and give both benih route glm budget minutes 1.
  Use TWO benih names so the assertion is meaningful.
- Launch two subprocesses concurrently:
  subprocess.Popen([sys.executable, "-m", "rumpun", "season", "start",
  str(yaml_path)], stdout=PIPE, stderr=PIPE, text=True) — rumpun is
  importable because pytest itself runs under uv run.
  Start both, then wait for both (communicate with a generous timeout,
  fail loudly on timeout).
- Assert: both exit 0; the final state.json parses; status "completed";
  the spawned map contains EACH benih name exactly once; the per-agent
  workspace state.json files exist for both.
- This is the proof that starter 2 blocked on state.lock and reattached
  instead of double-spawning.

Collab lane (protocol v2, NON-BLOCKING — evidence gathering only):
- RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK are exported to you.
- lane_tool.py: argv (kind, text) appends {"from": "w2", "kind": kind,
  "text": text} via rumpun.collab.append_event from the env vars; argv
  ("read", "") prints events. Post kind=start, kind=policy (the exact
  race assertion you coded), kind=done. Never wait on w1.

Rules: pytest only; ruff clean, line-length 100, py3.10+. notes.md: what
the test proves and any timing caveats you saw.
