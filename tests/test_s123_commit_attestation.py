"""s123 w2 pins - the commit attestation: the record names the lane's commit.

Spec source: the s123 w2 brief. Writers commit now; the run record cannot
say which commit a lane produced. Ground truth measured 2026-09-20: the
row builder reads src/rumpun/engine.py _agent_snap and _write_results
(the s112 gate pattern: additive keys, measured state untouched).

The mechanism: the engine records the repo HEAD at each lane's spawn
(head_at_spawn in the workspace state.json); at the terminal read, a lane
whose HEAD moved past it carries the new HEAD as an additive commit key
on the snap and the results row. The attestation names the commit
without judging it: a failed lane that committed still attests, running
and stalled snaps carry nothing, and a snap without the spawn record
keeps its shape. Scope follows the s112 precedent: additive keys only,
the failed and crashed vocabulary unchanged.

Fixture discipline: every pin builds a throwaway git repo under
tmp_path; the real campaign tree is never read or written.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 on the pre-attestation tree, pins 1, 4,
  6, 7, 8 (KeyError on the missing key); /tmp/s123-w2-pins-red.txt.
- GREEN captured 2026-09-20 post-attestation;
  /tmp/s123-w2-pins-green.txt.
- Pins 2, 3, and 5 are green on both sides by design: they pin the
  no-move clause, the shape clause, and the live-scope clause, so a
  later regression cannot attest an unmoved lane, a legacy
  workspace, or a running one.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from rumpun import engine

S123W2_STALL_S = 900.0
# no live pid's proc_start; the repo convention (the s112 pins)
S123W2_DEAD_PROC_START = 987654321


def _s123w2_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, f"git {args}: {proc.stderr}"
    return proc.stdout.strip()


def _s123w2_head(repo: Path) -> str:
    return _s123w2_git(repo, "rev-parse", "--short=12", "HEAD")


def _s123w2_advance(repo: Path) -> str:
    _s123w2_git(repo, "commit", "-q", "--allow-empty", "-m", "later work")
    return _s123w2_head(repo)


def _s123w2_proj(tmp_path: Path, route: str) -> tuple[Path, Path]:
    """A throwaway git repo holding the .rumpun scaffold, one clean commit."""
    repo = tmp_path / "proj"
    root = repo / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    (root / "runs").mkdir()
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        S123W2_PROJECT.format(route=route), encoding="utf-8"
    )
    (root / "prompts" / "dev" / "dummy.md").write_text(
        "prompt body\n", encoding="utf-8"
    )
    season = root / "seasons" / "s123f.yaml"
    season.write_text(S123W2_SEASON, encoding="utf-8")
    _s123w2_git(repo, "init", "-q", "-b", "main")
    _s123w2_git(repo, "config", "user.email", "fixture@example.invalid")
    _s123w2_git(repo, "config", "user.name", "fixture")
    _s123w2_git(repo, "add", "-A")
    _s123w2_git(repo, "commit", "-qm", "fixture base")
    return repo, season


def _s123w2_write_ws(
    repo: Path, sid: str, name: str,
    head: str | None, exit_code: str | None,
) -> Path:
    """Synthesize a dead writer workspace inside the fixture repo."""
    ws = repo / ".rumpun" / "runs" / sid / name
    ws.mkdir(parents=True, exist_ok=True)
    meta: dict[str, Any] = {
        "name": name,
        "route": "fixture",
        "cmd": "fixture-commit-attestation",
        "pid": 1,
        "proc_start": S123W2_DEAD_PROC_START,
        "started_at": time.time(),
    }
    if head is not None:
        meta["head_at_spawn"] = head
    (ws / "state.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    if exit_code is not None:
        (ws / "exit").write_text(exit_code, encoding="utf-8")
    return ws


S123W2_PROJECT = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "{route}"
"""

S123W2_SEASON = """\
id: s123f
goal: "fixture"
metric: "m"
mode: fight
methodology:
  approach: "x"
  evidence: []
  primary_change:
    type: add
    node: execute
    baseline: "b"
    expected_band: "WIN if x"
    rollback: "git revert"
    eval_window: "s123f"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
      reads: results.jsonl
benih:
  - name: w1
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 1}
stop:
  "on": [all_exited]
"""


def _s123w2_season_state(repo: Path, sid: str, names: tuple[str, ...]) -> None:
    """The running season state the finalize path reads."""
    season = repo / ".rumpun" / "runs" / sid / "_season"
    season.mkdir(parents=True, exist_ok=True)
    (season / "state.json").write_text(
        json.dumps(
            {
                "id": sid,
                "status": "running",
                "spawned": {
                    n: {"pid": 1, "proc_start": S123W2_DEAD_PROC_START}
                    for n in names
                },
            }
        ),
        encoding="utf-8",
    )


# pin 1 - the attestation at the snap layer: an exited writer whose repo
# HEAD moved past the recorded spawn HEAD carries the new HEAD as the
# additive commit key; state and exit_code stay the measured values.
def test_s123w2_exited_head_moved_carries_commit(tmp_path: Path) -> None:
    repo, _ = _s123w2_proj(tmp_path, "true")
    spawn_head = _s123w2_head(repo)
    moved = _s123w2_advance(repo)
    ws = _s123w2_write_ws(repo, "s123f", "w1", spawn_head, "0")
    snap = engine._agent_snap(ws, stall_s=S123W2_STALL_S)
    assert snap["state"] == "exited"
    assert snap["exit_code"] == 0
    assert snap["commit"] == moved


# pin 2 - the no-move clause (green on both sides by design): an exited
# writer whose HEAD never moved gains nothing; the record is the
# pre-attestation shape.
def test_s123w2_exited_head_unchanged_carries_nothing(tmp_path: Path) -> None:
    repo, _ = _s123w2_proj(tmp_path, "true")
    head = _s123w2_head(repo)
    ws = _s123w2_write_ws(repo, "s123f", "w1", head, "0")
    (ws / "notes.md").write_text("lane notes\n", encoding="utf-8")
    snap = engine._agent_snap(ws, stall_s=S123W2_STALL_S)
    assert snap["state"] == "exited"
    assert snap["exit_code"] == 0
    assert "commit" not in snap


# pin 3 - the shape clause (green on both sides by design): a snap
# without the spawn record keeps its shape even though the repo HEAD
# moved; legacy workspaces and non-repo roots attest nothing.
def test_s123w2_no_spawn_record_keeps_shape(tmp_path: Path) -> None:
    repo, _ = _s123w2_proj(tmp_path, "true")
    _s123w2_advance(repo)
    ws = _s123w2_write_ws(repo, "s123f", "w1", None, "0")
    snap = engine._agent_snap(ws, stall_s=S123W2_STALL_S)
    assert snap["state"] == "exited"
    assert "commit" not in snap


# pin 4 - no judgment: a failed writer whose HEAD moved still attests the
# commit; the failed vocabulary stays the honest state.
def test_s123w2_failed_lane_still_attests(tmp_path: Path) -> None:
    repo, _ = _s123w2_proj(tmp_path, "true")
    spawn_head = _s123w2_head(repo)
    moved = _s123w2_advance(repo)
    ws = _s123w2_write_ws(repo, "s123f", "w1", spawn_head, "1")
    snap = engine._agent_snap(ws, stall_s=S123W2_STALL_S)
    assert snap["state"] == "failed"
    assert snap["exit_code"] == 1
    assert snap["commit"] == moved


# pin 5 - the live-scope clause (green on both sides by design): a
# running snap carries no commit key even though the repo HEAD moved;
# the attestation reads at exit, not mid-flight.
def test_s123w2_running_snap_carries_no_commit(
    tmp_path: Path, monkeypatch: Any,
) -> None:
    repo, _ = _s123w2_proj(tmp_path, "true")
    spawn_head = _s123w2_head(repo)
    _s123w2_advance(repo)
    ws = _s123w2_write_ws(repo, "s123f", "w1", spawn_head, None)
    monkeypatch.setattr(engine, "_alive", lambda pid, start: True)
    snap = engine._agent_snap(ws, stall_s=S123W2_STALL_S)
    assert snap["state"] == "running"
    assert "commit" not in snap


# pin 6 - the season record: the finalize passes the commit key into the
# results row, and a lane with no HEAD move keeps the bare row.
def test_s123w2_row_carries_commit_and_bare_row_stays_bare(
    tmp_path: Path,
) -> None:
    repo, _ = _s123w2_proj(tmp_path, "true")
    base = _s123w2_head(repo)
    w1 = _s123w2_write_ws(repo, "s123f", "w1", base, "0")
    (w1 / "notes.md").write_text("lane notes\n", encoding="utf-8")
    moved = _s123w2_advance(repo)
    w2 = _s123w2_write_ws(repo, "s123f", "w2", moved, "0")
    (w2 / "notes.md").write_text("lane notes\n", encoding="utf-8")
    _s123w2_season_state(repo, "s123f", ("w1", "w2"))
    state = engine._finalize(repo / ".rumpun", "s123f", "completed", {})
    assert state["agents"]["w1"]["commit"] == moved
    assert state["agents"]["w1"]["state"] == "exited"
    assert "commit" not in state["agents"]["w2"]
    path = repo / ".rumpun" / "runs" / "s123f" / "results.jsonl"
    rows = {
        json.loads(ln)["unit"]: json.loads(ln)
        for ln in path.read_text(encoding="utf-8").splitlines()
    }
    assert rows["w1"]["commit"] == moved
    assert rows["w1"]["state"] == "exited"
    assert "commit" not in rows["w2"]


# pin 7 - the spawn side: start_season records the repo HEAD at each
# lane's spawn (head_at_spawn in the workspace state.json); a lane that
# never moves stays bare end to end.
def test_s123w2_spawn_records_head_no_move_stays_bare(tmp_path: Path) -> None:
    repo, season = _s123w2_proj(tmp_path, "echo lane notes > notes.md")
    before = _s123w2_head(repo)
    state = engine.start_season(season, repo / ".rumpun")
    assert state["status"] == "completed"
    ws_meta = json.loads(
        (repo / ".rumpun" / "runs" / "s123f" / "w1" / "state.json")
        .read_text(encoding="utf-8")
    )
    assert ws_meta["head_at_spawn"] == before
    assert "commit" not in state["agents"]["w1"]


# pin 8 - end to end: a lane that commits carries its commit on the
# agents entry and the results row; the season stays completed (the
# attestation names the commit without judging it).
def test_s123w2_season_row_names_lane_commit(tmp_path: Path) -> None:
    repo, season = _s123w2_proj(
        tmp_path,
        "echo lane notes > notes.md;"
        " git -C ../../../.. commit -q --allow-empty -m lane",
    )
    state = engine.start_season(season, repo / ".rumpun")
    assert state["status"] == "completed"
    final = _s123w2_head(repo)
    assert state["agents"]["w1"]["commit"] == final
    assert state["agents"]["w1"]["state"] == "exited"
    row = json.loads(
        (repo / ".rumpun" / "runs" / "s123f" / "results.jsonl")
        .read_text(encoding="utf-8")
    )
    assert row["commit"] == final
    assert row["state"] == "exited"
