# Task: write report.py (P36 surface 2: static season report)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s2/w4. Write ONLY report.py, notes.md.

Interface that already exists in rumpun.engine (do NOT write it):
  def read_status(root: Path, sid: str) -> dict
    keys: id, status, started_at, ended_at, agents{name: {name, route, state, exit_code, seconds}}

API to write:
  def render_report(root: Path, sid: str, out: Path | None = None) -> Path
  - renders a self-contained HTML report to root/rimba/<sid>/report.html (or out).
  - No external assets, no JavaScript, no network. All dynamic text through
    html.escape.
  - Content: season id, status, start/end ISO times, duration, per-agent table
    (name, route, state, exit code, seconds), and a provenance legend with the
    three labels [H] harness-observed, [A] agent-authored, [D] derived.
  - Deterministic: identical state must produce byte-identical HTML (sort keys,
    no timestamps of your own).

In notes.md: one paragraph on what a STALE marker would need (hash comparison).
Same constraints: stdlib only, logging not print, ruff-clean 100, py3.10+, workspace only.
