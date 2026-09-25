# Task: implement the P8 directives channel as `rumpun direct` (full cli.py into workspace)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s7/w1. Write ONLY cli.py,
notes.md, lane_tool.py into this workspace. Do not touch anything outside it.

Base your cli.py on the CURRENT repo file
/mnt/data/work/rumpun/src/rumpun/cli.py (read it first; keep every behavior
and all 20 tests passing; do not edit tests/).

P8 (DESIGN.md): directives are the human seat's channel; nothing is injected
into a running process; the artifact records pending versus consumed.

Implement a TOP-LEVEL verb (not under season):
  rumpun direct TEXT            # append one directive, status pending
  rumpun direct --list          # print all directives, pending first
- Storage: .rumpun/akar/directives.jsonl + .rumpun/akar/directives.lock.
  Append via the EXISTING tested module — do not write a new lock:
    from rumpun import collab
    event = collab.append_event(
        {"file": str(root / "akar" / "directives.jsonl"),
         "lock": str(root / "akar" / "directives.lock")},
        "operator", {"text": text, "status": "pending"},
    )
  seq and the flock come from collab for free.
- --list prints one line per event: "seq  status  text"; pending lines
  first, then consumed, each group in seq order. Empty file: print
  "no directives".
- root from _project_root(Path.cwd()); the akar dir exists in every
  scaffolded project; create directives.jsonl/lock on first use via
  append_event (collab opens "a", never truncates).
- Remove "direct" from SEASON_STUBS (the registry becomes empty: drop the
  dict AND its stub loop if empty — keep the loop code but guard with
  `if SEASON_STUBS:`). Docstring version note becomes v0.7.0, and "direct"
  moves into the Implemented line as: `direct [--list]`.

Collab lane (protocol v2, NON-BLOCKING — evidence gathering only):
- RUMPUN_LANE_FILE / RUMPUN_LANE_LOCK are exported to you.
- lane_tool.py: argv (kind, text) appends {"from": "w1", "kind": kind,
  "text": text} via rumpun.collab.append_event from the env vars; argv
  ("read", "") prints events. Post kind=start, kind=policy (your exact
  CLI contract), kind=done. Never wait on w2.

Rules: stdlib only; the verb's own output may print. ruff clean,
line-length 100, py3.10+. notes.md: the contract you posted.
