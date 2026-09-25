"""s143 w2 pins - the fixed pipeline proves real lane work.

Spec source: the s143 w2 brief. The s142 LOSS left the template-seeded
season's lanes running the generic prompt and producing nothing (an
empty sweep.jsonl, three "notes.md missing" gate marks). w1 landed the
per-lane briefs in the scaffold; this lane walks the fixed pipeline end
to end in a tmp campaign and proves the lanes produce real work:

- the walk: init a tmp campaign, seed the steady-state season from the
  scaffolded _steady-state.yaml template, point the three writers at
  light stub routes, and run engine.start_season to a terminal state.
- the briefs ride in: each lane's prompt-meta.yaml names its per-lane
  brief (not the generic execute.md) and the prompt carries the notes
  contract.
- the artifacts carry lane work: each lane's named record exists, and
  its row quotes the brief line naming the artifact (a generic prompt
  leaves the work field empty and the pin names the drift).
- the notes exist: every lane's notes.md is present and non-empty.
- the gate is clean: the results rows all exited 0 with no
  "incomplete" key -- the s142 mark gone.

The stub route (tools/light_lane.sh in the tmp project) is the light
stand-in for a writer: it reads the lane's prompt.md and records what
the brief names. It is not a model; the pin proves the pipeline
delivers the briefs and the lanes answer in their named artifacts.

Bounds honored: everything runs in pytest's tmp_path (the tmp-campaign
convention: init in tmp, the real campaign never touched); offline;
seconds-fast.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from rumpun import engine, scaffold

# writer name -> (artifact, route key, brief file beside the template)
LANES = (
    ("sweep", "sweep.jsonl", "light-sweep", "_steady-state-lint-sweep.md"),
    ("probes", "probes.jsonl", "light-probes", "_steady-state-route-probes.md"),
    ("rehearsal", "rehearsals.jsonl", "light-rehearsal", "_steady-state-rehearsals.md"),
)

LIGHT_LANE_SH = """\
#!/bin/sh
# light lane stub (s143 w2): read the brief, record the named artifact.
art=$1; lane=$2; prompt=$3
line=$(grep -m1 -F "$art" "$prompt" || true)
printf '{"lane": "%s", "artifact": "%s", "work": "%s"}\\n' \\
    "$lane" "$art" "$line" > "$art"
printf 'lane %s worked from the brief (prompt.md names %s) and recorded %s\\n' \\
    "$lane" "$art" "$art" > notes.md
"""


def _walk(tmp_path: Path) -> tuple[dict, Path]:
    """The pipeline walk: init, seed from the template, run it light."""
    proj = tmp_path / "proj"
    scaffold.init_project(proj)
    root = proj / ".rumpun"
    script = proj / "tools" / "light_lane.sh"
    script.write_text(LIGHT_LANE_SH, encoding="utf-8")
    cfg_path = root / "rumpun.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg["routes"] = {
        route: f"sh {script} {artifact} {lane} {{prompt}}"
        for lane, artifact, route, _ in LANES
    }
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    template = yaml.safe_load(
        (root / "seasons" / "_steady-state.yaml").read_text(encoding="utf-8"),
    )
    season_path = root / "seasons" / "s1.yaml"
    season_path.write_text(
        yaml.safe_dump(template, sort_keys=False), encoding="utf-8"
    )
    season = yaml.safe_load(season_path.read_text(encoding="utf-8"))
    assert [w["name"] for w in season["writers"]] == [lane for lane, *_ in LANES]
    for writer, (_, _, route, _) in zip(season["writers"], LANES, strict=True):
        writer["route"] = route
    season_path.write_text(
        yaml.safe_dump(season, sort_keys=False), encoding="utf-8"
    )
    state = engine.start_season(season_path, root)
    return state, root


def test_s143w2_walk_completes_with_all_lanes_exited(tmp_path: Path) -> None:
    """Pin 1: the walk runs to a completed season, every lane exited 0."""
    state, _root = _walk(tmp_path)
    assert state["status"] == "completed"
    snaps = state["agents"]
    assert set(snaps) == {lane for lane, *_ in LANES}
    for snap in snaps.values():
        assert snap["state"] == "exited", snap
        assert snap["exit_code"] == 0, snap


def test_s143w2_lane_prompts_carry_the_per_lane_briefs(tmp_path: Path) -> None:
    """Pin 2: the briefs rode in; the generic prompt is gone."""
    _state, root = _walk(tmp_path)
    for lane, _, _, brief in LANES:
        ws = root / "runs" / "s1" / lane
        meta = (ws / "prompt-meta.yaml").read_text(encoding="utf-8")
        assert f"template: seasons/{brief}" in meta, f"{lane}: {meta}"
        assert "prompts/base/execute.md" not in meta, f"{lane}: {meta}"
        prompt = (ws / "prompt.md").read_text(encoding="utf-8")
        assert "notes.md REQUIRED" in prompt, f"{lane}: generic prompt, no notes contract"


def test_s143w2_artifacts_carry_lane_work(tmp_path: Path) -> None:
    """Pin 3: each named record exists and quotes its brief's lane work."""
    _state, root = _walk(tmp_path)
    for lane, artifact, _, _brief in LANES:
        row = (root / "runs" / "s1" / lane / artifact).read_text(encoding="utf-8")
        assert row.strip(), f"{lane}: {artifact} empty (no lane work)"
        match = re.search(r'"work": "(.*)"', row)
        assert match, f"{lane}: no work field in {artifact}"
        work = match.group(1)
        assert artifact in work, (
            f"{lane}: brief never named {artifact} (generic prompt drift)"
        )
        assert work != artifact, (
            f"{lane}: work field carries no brief line (generic prompt drift)"
        )


def test_s143w2_notes_exist_in_every_lane(tmp_path: Path) -> None:
    """Pin 4: every lane left notes.md; the s142 absence is gone."""
    _state, root = _walk(tmp_path)
    for lane, *_ in LANES:
        notes = (root / "runs" / "s1" / lane / "notes.md").read_text(encoding="utf-8")
        assert notes.strip(), f"{lane}: notes.md empty"


def test_s143w2_results_rows_carry_no_incomplete_mark(tmp_path: Path) -> None:
    """Pin 5: the gate is clean -- all rows exited 0, no incomplete key."""
    _state, root = _walk(tmp_path)
    text = (root / "runs" / "s1" / "results.jsonl").read_text(encoding="utf-8")
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    assert len(rows) == len(LANES), rows
    for row in rows:
        assert row["exit_code"] == 0, row
        assert "incomplete" not in row, row
