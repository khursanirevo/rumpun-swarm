# Task: write src/rumpun/collab.py (engine-grade collab lane files)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s3/w1. Write ONLY collab.py,
notes.md into this workspace. Do not touch anything outside it.

Context: rumpun seasons spawn one-shot agents (benih) in separate workspaces
(fight mode). We are adding engine-supported collaboration: benih entries that
declare `collab: <group>` will share a lane file plus lock file, and the engine
will export their paths as env vars so agents coordinate by appending JSON
events. The engine will call your module exactly like this (already decided,
do not write it):

  lanes[g] = collab.prepare_lane(root, sid, g)   # root is the .rumpun dir
  env = {**os.environ,
         "RUMPUN_LANE_FILE": lanes[g]["file"],
         "RUMPUN_LANE_LOCK": lanes[g]["lock"]}

API to write (module rumpun.collab):

  class LaneError(Exception)

  def prepare_lane(root: Path, sid: str, group: str) -> dict[str, str]
  - root/rimba/<sid>/_season/lane-<group>.jsonl and lane-<group>.lock are
    created if missing; existing files are never truncated. Returns
    {"file": "<abs path>", "lock": "<abs path>"}.

  def append_event(lane: dict[str, str], sender: str, payload: dict) -> dict
  - fcntl.flock LOCK_EX on the lock file; seq = number of existing event
    lines; append exactly one line:
    json.dumps({"seq": n, "from": sender, **payload}, sort_keys=True) + "\n";
    then unlock and close. Returns the event dict as written.

  def read_events(lane: dict[str, str]) -> list[dict]
  - parse the file, skip blank lines, return events in file order. A line
    that fails json.loads raises LaneError naming the 1-based line number.

Rules: stdlib only (fcntl ok; linux-only is fine). logging, never print.
ruff clean at line-length 100, py3.10+. No clock reads, no randomness.

notes.md: one paragraph — how two agents should use RUMPUN_LANE_FILE to hand
work to each other, and why flock makes read-then-append safe for both.
