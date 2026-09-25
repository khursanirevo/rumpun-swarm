# s19 w1 notes — H2 identity-checked termination + H3 agents run in their workspace

Review source: akar codex-review-2026-09-14 (findings H2, H3).
All verification ran against patched copies in this scratch tree
(`scratch/` = full repo copy; the real tree is untouched by w1).

## What changed

One file: `scratch/src/rumpun/engine.py` (merge artifact copied to
`engine.py` beside these notes).

**H2 — `_terminate(ws, pid, proc_start)`** (was `_terminate(ws, pid)`):
requires the spawn-recorded proc_start. Before the first signal it
re-checks `_proc_start_ticks(pid) == proc_start`. On mismatch (recycled
pid or already-gone) it logs one WARNING with the workspace path and both
start ticks (never process content), writes no `terminated` marker, and
skips signaling entirely. On a passed check the behavior is unchanged:
marker before SIGTERM, 5s grace poll, SIGKILL. The only internal caller —
`_finalize`'s kill loop — now passes `meta.get("proc_start")` from
`state["spawned"]`. Full diff readback against the real tree showed only
the five intended hunks (module docstring, `_terminate`, the finalize call
site, the workspace resolve, Popen cwd).

**H3 — agents run inside their workspace:** `start_season` resolves the
workspace before spawning, `ws = (season_dir(root, sid) / name).resolve()`,
and Popen gains `cwd=ws`. The wrapper's `{prompt}` and exit-file paths
become absolute as a result, so every route shape in rumpun.yaml
(`cat {prompt} | claude ...`, `env -u ... sh -c 'cat {prompt} | ...'`,
`codex exec ... {prompt}`) stays cwd-independent. No route or scaffold text
needed changes; routes.py and scaffold.py are untouched.

## Verification (verified real)

Suite against the patched scratch copies, zero skips (full log:
`scratch/pytest.log`):

    84 passed in 21.84s
    pytest-exit=0

H2 repro (`repro_h2_h3.py`; a wrong proc_start simulates the recycled pid
slot). Verbatim from `scratch/repro-output.txt` (final clean run; the
script exits 0 only when every check passes):

    INFO --- H2: identity-checked termination ---
    WARNING /mnt/data/tmp/h2-ws-uxh9b38f: pid 3011197 identity mismatch (recorded start 3194489, live 3182144); not signaled
    INFO H2 mismatch: not_signaled=True warned=True marker_absent=True (pid 3011197, recorded start 3194489, live start 3182144)
    INFO H2 control: signaled_and_dead=True marker_written=True

H3 repro (same run; a pwd route and a `cat {prompt}` route through a real
`engine.start_season`):

    INFO --- H3: agents run inside their workspace ---
    INFO spawned w1 (stub) pid 3011198
    INFO spawned w2 (stubcat) pid 3011199
    INFO season h3 -> completed
    INFO H3: status=completed pwd_in_log=/mnt/data/tmp/h3-proj-qc5gsybq/.rumpun/rimba/h3/w1 equals_workspace=True cat_route_replayed_prompt=True exits=['0', '0']
    INFO H3 workspace path: /mnt/data/tmp/h3-proj-qc5gsybq/.rumpun/rimba/h3/w1
    INFO RESULT: H2=PASS H3=PASS

ruff (`--no-respect-gitignore`; this tree sits under gitignored rimba/):
`All checks passed!` on `repro_h2_h3.py` and `src/rumpun/engine.py`.

## Deferred, per task scope

The review's second half of H2 — crashed leaders leaving live descendants
(group members outliving a dead leader) — is NOT addressed. It needs a
group-membership sweep (subreaper or a /proc pgid scan), which is not
trivial. Noted for a later season.

## Decisions recorded

- Marker policy on mismatch: when signaling is skipped, no `terminated`
  marker is written, so the snapshot honestly reads `crashed` (nothing was
  terminated). On the passed path the marker still precedes the first
  signal, so the s2/s4 marker-ordering fix holds.
- Recorded `proc_start=None` can only match a gone process (live ticks
  None). A live process with no recorded identity is treated as mismatch
  and never signaled.

## Artifacts

- `engine.py` — patched engine copy (merge artifact)
- `scratch/src/rumpun/engine.py` — the verified patched copy
- `scratch/repro_h2_h3.py` — repro script (ruff clean)
- `scratch/repro-output.txt` — captured repro output (source of the
  verbatim blocks above)
- `scratch/pytest.log` — full suite log
- `lane.py` — lane event helper used for this season's build lane
