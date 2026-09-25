# Task: write harvest.py (rumpun build-order step 4, season close)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s2/w2. Write ONLY harvest.py, notes.md.

Assume this exact interface already exists in package rumpun, module akar (do NOT write it):
  class AkarError(Exception)
  def append_record(root: Path, record_id: str, title: str, body: str) -> Path
  def find_record(root: Path, record_id: str) -> Path

Assume this exists in rumpun.engine (do NOT write it):
  def read_status(root: Path, sid: str) -> dict
    keys: id, status, started_at, ended_at, agents{name: {name, route, state, exit_code, seconds}}
  class EngineError(Exception)

API to write:
  def harvest_season(root: Path, sid: str, verdict: str, implies: str) -> Path
  - verdict must be WIN|LOSS|NEUTRAL|INVALID, else raise ValueError.
  - reads engine.read_status(root, sid); builds akar record_id f"{sid}-harvest" via
    akar.append_record; body = season status, duration, per-agent state table
    (markdown), then "verdict: <verdict>" and "implies: <implies>".
  - returns the record path.

In notes.md: describe the CLI wiring you would add (season harvest <id> --verdict V --implies TEXT).
Same constraints: stdlib only, logging not print, ruff-clean 100, py3.10+, workspace only.
