# Task: implement rumpun season list and update the README

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s5/w3. Write ONLY cli.py,
README.md, notes.md into this workspace. Do not touch anything outside it.

Base both on the CURRENT repo files /mnt/data/work/rumpun/src/rumpun/cli.py
and /mnt/data/work/rumpun/README.md (read them first; keep every behavior
and test passing).

cli.py:
- Replace the season list stub with a real verb: walks .rumpun/musim/s*.yaml
  ids in order and prints one line per season:
    s3  completed  851s  3 agents
    s4  stopped_stall  901s  3 agents
  Reads each season's rimba/<id>/_season/state.json (status, duration
  ended-started, agent count); a season with no state prints "no state".
  Sorted by season number. No new deps; _project_root for root.
- Keep list under the season group. Update the docstring version note.

README.md:
- Move `season list` out of "Not implemented yet" into the quickstart
  (after board), one line under it.
- Add report --serve to the quickstart section for season report: renders
  then serves rimba/ on http://localhost:8611 (<sid>/report.html), Ctrl-C
  exits 0.
- Leave the remaining stubs listed honestly.

Rules: stdlib only; logging, never print (list output may print: it is the
verb's output). ruff clean, line-length 100, py3.10+. notes.md: what you
checked to keep commands real.
