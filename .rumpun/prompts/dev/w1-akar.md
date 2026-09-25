# Task: write akar.py (rumpun build-order step 4, record writer)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s2/w1. Write ONLY these files inside your workspace: akar.py, notes.md.

API (exact signatures):
  class AkarError(Exception): ...
  def append_record(root: Path, record_id: str, title: str, body: str) -> Path
  def find_record(root: Path, record_id: str) -> Path

Behavior:
- root is the project .rumpun directory.
- append_record writes root/akar/<YYYY-MM-DD>_<record_id>.md :
  header "# akar record: <record_id>", lines "id:", "date:", "title:", then body,
  then a final line "sha256: <hex>" computed over the body.
- Raises AkarError if any existing file in akar/ already declares this record_id.
- Append-only: never modify existing records. Atomic write (tmp file + rename).
- find_record returns the path or raises AkarError.

Constraints: stdlib only. logging, never print. ruff-clean, line length 100. Python 3.10+.
Do NOT create, modify, or delete anything outside your workspace.
