# Task: write evolve.py (rumpun build-order step 5, evolusi deterministic v0)

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s2/w3. Write ONLY evolve.py, notes.md.

Interfaces that already exist in package rumpun (do NOT write them):
  yamlio.load(path) -> dict (rejects duplicate keys), yamlio.YamlError
  lint.lint(path) -> list of Finding(severity: str, message: str, path: str)
  akar.find_record(root, record_id) -> Path, akar.AkarError

API to write:
  class EvolveError(Exception)
  def draft_next(root: Path, parent_yaml: Path) -> Path
  - parent season YAML must have id matching s<N>; next id is s<N+1> with N+1 = max
    existing musim/s*.yaml number + 1.
  - writes .rumpun/musim/s<N+1>.yaml: parent's id->new id, parent: <parent id>,
    goal/metric/mode/benih/stop copied verbatim, methodology with
    evidence: [] and primary_change skeleton:
      type: add
      node: execute
      baseline: ""
      expected_band: ""
      rollback: ""
      eval_window: ""
  - raises EvolveError if the target file already exists.
  def apply(root: Path, drafted: Path) -> None
  - run lint.lint(drafted); if ANY error-severity finding exists, raise EvolveError
    carrying the messages (empty primary_change fields must block apply).

In notes.md: 5 lines on how an evolver agent would fill the skeleton with akar citations.
Same constraints: stdlib only, logging not print, ruff-clean 100, py3.10+, workspace only.
