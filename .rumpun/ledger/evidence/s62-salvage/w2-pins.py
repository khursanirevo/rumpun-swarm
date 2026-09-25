"""s62 w2 pins — the salvage marker, specified before it exists.

Spec-first pins (red against current code) for the s62 contract (w1 brief
.rumpun/runs/s62/w1/prompt.md; ledger anchors 2026-09-16_s59-harvest — a
stopped_stall season harvested WIN with nothing marking the salvage — and
2026-09-16_usefulness-decade-5 residual 7: "Salvaged stopped seasons earn
WIN alongside completed seasons. Aggregate verdicts obscure execution
reliability and intervention costs."). Spec anchors, the measured red set,
and surface assumptions: .rumpun/runs/s62/w2/notes.md.

Contract these pins hold — every pin runs the real verbs end to end
(`rumpun season start` / `rumpun harvest` / `rumpun audit` as bounded
subprocesses over tmp .rumpun projects):

1. The salvaged world: harvesting a stopped_stall fixture marks the close
   on both surfaces — the season's verdict row carries "salvaged": true
   and the harvest record's title carries "(salvaged)" — while a completed
   fixture harvested the same way stays unmarked on both surfaces.
2. The histogram split: after the marking, a fresh `rumpun audit` over a
   campaign holding one salvaged win and one completed win renders the
   agreed F3 split form "2 WIN (1 salvaged), 0 LOSS, 0 INVALID", reading
   the rows as they stand (no record rewritten).
3. Immutability: the marking writes only new rows and records — every
   ledger and run-tree byte that existed before the harvest stays
   byte-identical, the pre-existing verdict rows survive verbatim as a
   strict prefix of the marked file, and the only new files are the
   harvest record and akar's append lock.

Red history (measured; full runs in notes.md): RED-SET-PLACEHOLDER

Grafting: drop this file into tests/ as-is. Helpers carry the _s62w2_
prefix, so nothing collides with existing defs. No pin touches the real
repo, ledger, or any live season: every fixture lives in pytest
tmp_path. Each run is bounded twice — S62W2_TIMEOUT on the subprocess
and each benih's own 1-minute budget inside the engine — and the dead
stub self-exits at 91s, so a wedged engine ends the run itself and the
suite never hangs.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

S62W2_TIMEOUT = 240  # bounds one subprocess (task bound); the benih budget bounds harder
S62W2_STALL_MINUTES = 0.1  # the 6s stall window the stopped_stall fixture uses
S62W2_SID_A = "s621"  # lint requires the s<N> id shape; no real row is touched
S62W2_SID_B = "s622"
S62W2_SID_C = "s623"

S62W2_ROUTES = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  stub: 'printf ''%s\\n'' ''{"unit":"u1","verdict":"PASS"}'' > results.jsonl'
  plain: 'cat {prompt} > /dev/null'
  dead: 'i=0; while [ "$i" -le 90 ]; do i=$((i+1)); sleep 1; done'
"""

S62W2_SEASON_YAML = """\
id: {sid}
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
    eval_window: "{sid}"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
      reads: results.jsonl
writers:
  - name: w1
    route: {route}
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [{stop}]
"""

S62W2_COMPLETED_STOP = "all_exited"
S62W2_STALL_STOP = 'all_exited, {{stall_minutes: {stall}}}'


def _s62w2_root() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and in
    tests/ (post-graft): both sit under the repo root. For a HEAD
    extraction the walk-up lands in the extraction, so the subprocesses
    import that extraction's src, never the live tree.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s62w2_proj(tmp_path: Path) -> tuple[Path, Path]:
    """One tmp campaign (.rumpun layout) under a fresh directory.

    Returns (project dir, .rumpun root). The routes are shell stubs:
    `stub` consumes the prompt, writes one results.jsonl row in its own
    workspace, and exits 0; `plain` consumes the prompt and exits 0
    writing nothing; `dead` writes nothing for 91s so the stall rule can
    stop the season first. The 1-minute benih budget bounds any wedged
    watcher inside the engine itself.
    """
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    (root / "runs").mkdir()
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(S62W2_ROUTES, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    return root.parent, root


def _s62w2_season(root: Path, sid: str, route: str, stop: str) -> Path:
    """Write one season yaml into the campaign's seasons dir; return its path."""
    season = root / "seasons" / f"{sid}.yaml"
    season.write_text(
        S62W2_SEASON_YAML.format(sid=sid, route=route, stop=stop), encoding="utf-8",
    )
    return season


def _s62w2_stall_stop() -> str:
    """The stop rule for the stopped_stall fixture, braces pre-escaped."""
    return S62W2_STALL_STOP.format(stall=S62W2_STALL_MINUTES)


def _s62w2_env() -> dict[str, str]:
    """Subprocess env: PYTHONPATH pins the repo src over any editable .pth."""
    env = dict(os.environ)
    env["PYTHONPATH"] = (
        str(_s62w2_root() / "src") + os.pathsep + env.get("PYTHONPATH", "")
    )
    return env


def _s62w2_run(proj: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    """One bounded CLI verb over the campaign; cwd = the project dir, so the
    root walk-up from cwd resolves this campaign."""
    return subprocess.run(
        [sys.executable, "-m", "rumpun", *argv],
        cwd=str(proj), env=_s62w2_env(), capture_output=True, text=True,
        timeout=S62W2_TIMEOUT,
    )


def _s62w2_start(tmp_path: Path, season: Path) -> subprocess.Popen[str]:
    """Launch the watcher CLI over the fixture; PYTHONPATH pins the repo src."""
    return subprocess.Popen(
        [sys.executable, "-m", "rumpun", "season", "start", str(season)],
        cwd=str(tmp_path), env=_s62w2_env(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )


def _s62w2_terminal(proc: subprocess.Popen[str], root: Path, sid: str) -> dict[str, Any]:
    """Bounded wait for any terminal status; the persisted state, read fresh.

    The watcher rewrites state.json atomically (tmp + replace), so a read
    is never torn; polling stops at the first terminal status.
    """
    state_path = root / "runs" / sid / "_season" / "state.json"

    def read_terminal() -> dict[str, Any] | None:
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return None if state.get("status") == "running" else state

    deadline = time.monotonic() + S62W2_TIMEOUT
    while time.monotonic() < deadline:
        state = read_terminal()
        if state is not None:
            return state
        if proc.poll() is not None:
            _out, err = proc.communicate(timeout=30)
            raise AssertionError(
                f"watcher exited before a terminal state (rc={proc.returncode});"
                f" stderr:\n{err}"
            )
        time.sleep(0.05)
    raise AssertionError(
        f"season {sid} never reached a terminal state in {S62W2_TIMEOUT}s"
    )


def _s62w2_finish(proc: subprocess.Popen[str]) -> tuple[int, str]:
    """Drain the watcher subprocess, bounded; (returncode, stderr)."""
    try:
        _out, err = proc.communicate(timeout=S62W2_TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise
    return proc.returncode, err


def _s62w2_complete(
    tmp_path: Path, root: Path, sid: str, route: str,
) -> dict[str, Any]:
    """Run one season start to a terminal state; the persisted state."""
    season = _s62w2_season(root, sid, route, S62W2_COMPLETED_STOP)
    if route == "dead":
        season = _s62w2_season(root, sid, route, _s62w2_stall_stop())
    proc = _s62w2_start(tmp_path, season)
    state = _s62w2_terminal(proc, root, sid)
    _rc, err = _s62w2_finish(proc)
    assert state["status"] == ("stopped_stall" if route == "dead" else "completed"), (
        f"season {sid} ended {state['status']}; stderr:\n{err}"
    )
    return state


def _s62w2_harvest(proj: Path, sid: str) -> subprocess.CompletedProcess[str]:
    """One bounded `rumpun harvest` close over the fixture; rc asserted 0."""
    ran = _s62w2_run(proj, "harvest", sid, "--verdict", "WIN", "--implies", "fixture close")
    assert ran.returncode == 0, (
        f"rumpun harvest {sid} exited {ran.returncode}; stderr:\n{ran.stderr}"
    )
    return ran


def _s62w2_harvest_record(root: Path, sid: str) -> str:
    """The close record's text: the one <date>_<sid>-harvest.md in the ledger."""
    matches = sorted((root / "ledger").glob(f"*_{sid}-harvest.md"))
    assert len(matches) == 1, (
        f"expected exactly one {sid}-harvest record in {root / 'ledger'},"
        f" found {[p.name for p in matches]}"
    )
    return matches[0].read_text(encoding="utf-8")


def _s62w2_title(record: str) -> str:
    """The record's title line content (akar layout: title is the 4th line)."""
    line = next(ln for ln in record.splitlines() if ln.startswith("title: "))
    return line[len("title: "):]


def _s62w2_season_rows(root: Path, sid: str) -> list[dict[str, Any]]:
    """The season's verdicts.jsonl rows, parsed."""
    path = root / "runs" / sid / "verdicts.jsonl"
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _s62w2_season_row(root: Path, sid: str) -> dict[str, Any]:
    """The one season-level verdict row for sid (the row the close wrote)."""
    rows = [r for r in _s62w2_season_rows(root, sid) if r.get("season") == sid]
    assert len(rows) == 1, f"expected one season-level row for {sid}, got {rows}"
    return rows[0]


# --- pin 1: the salvaged world ----------------------------------------------------


def test_s62w2_stalled_close_marks_and_completed_stays_unmarked(tmp_path: Path) -> None:
    """Harvesting a stopped_stall fixture marks both surfaces; completed does not.

    The salvaged fixture: a dead-stub season stopped by the stall rule,
    closed with `rumpun harvest`. Its verdict row must carry
    "salvaged": true and the harvest record's title must carry
    "(salvaged)". The completed fixture: the same close over a season
    whose agent exited 0 — its row must not be marked and its title must
    not carry the marker. On main today the close marks neither (the row
    has no salvaged key, the title is plain "season <sid> harvest"), so
    the pin is red until w1's change lands.
    """
    proj, root = _s62w2_proj(tmp_path)
    _s62w2_complete(tmp_path, root, S62W2_SID_A, "dead")
    _s62w2_harvest(proj, S62W2_SID_A)
    salvaged_row = _s62w2_season_row(root, S62W2_SID_A)
    assert salvaged_row.get("verdict") == "WIN", f"fixture row: {salvaged_row}"
    assert salvaged_row.get("salvaged") is True, (
        f"the stopped_stall close left no salvage mark on the row: {salvaged_row}"
    )
    salvaged_title = _s62w2_title(_s62w2_harvest_record(root, S62W2_SID_A))
    assert "(salvaged)" in salvaged_title, (
        f"the stopped_stall close record title is unmarked: {salvaged_title!r}"
    )

    _s62w2_complete(tmp_path, root, S62W2_SID_B, "stub")
    _s62w2_harvest(proj, S62W2_SID_B)
    completed_row = _s62w2_season_row(root, S62W2_SID_B)
    assert completed_row.get("verdict") == "WIN", f"fixture row: {completed_row}"
    assert completed_row.get("salvaged") is not True, (
        f"a completed close must stay unmarked: {completed_row}"
    )
    completed_title = _s62w2_title(_s62w2_harvest_record(root, S62W2_SID_B))
    assert "(salvaged)" not in completed_title, (
        f"a completed close record title must not carry the marker: {completed_title!r}"
    )
    logger.info("pin 1 held: salvaged close marked, completed close unmarked")


# --- pin 2: the histogram split ----------------------------------------------------


def test_s62w2_audit_splits_salvaged_from_completed_wins(tmp_path: Path) -> None:
    """A fresh audit renders the salvaged split in the F3 line.

    One stopped_stall season closed WIN (marked) and one completed season
    closed WIN, then one fresh `rumpun audit` reads the campaign. The F3
    verdict histogram must render the agreed split form — "2 WIN
    (1 salvaged), 0 LOSS, 0 INVALID" — reading the rows as they stand.
    On main today the same campaign renders the bare aggregate
    "WIN 2, LOSS 0, INVALID 0", so the pin is red until w1's change
    lands.
    """
    proj, root = _s62w2_proj(tmp_path)
    _s62w2_complete(tmp_path, root, S62W2_SID_A, "dead")
    _s62w2_harvest(proj, S62W2_SID_A)
    _s62w2_complete(tmp_path, root, S62W2_SID_B, "stub")
    _s62w2_harvest(proj, S62W2_SID_B)
    ran = _s62w2_run(proj, "audit", "--last", "10")
    assert ran.returncode == 0, (
        f"rumpun audit exited {ran.returncode}; stderr:\n{ran.stderr}"
    )
    records = sorted((root / "ledger").glob("*audit-*.md"))
    assert records, f"the audit wrote no record into {root / 'ledger'}"
    record = records[-1].read_text(encoding="utf-8")
    f3 = next(
        (ln for ln in record.splitlines() if ln.startswith("F3 verdict histogram")),
        "",
    )
    assert f3, f"the fresh audit carries no F3 line:\n{record}"
    assert "2 WIN (1 salvaged), 0 LOSS, 0 INVALID" in f3, (
        f"the F3 histogram does not split salvaged from completed wins: {f3}"
    )
    logger.info("pin 2 held: F3 split rendered: %s", f3)


# --- pin 3: the marking is append-only ---------------------------------------------


def test_s62w2_marking_writes_only_new_rows_and_records(tmp_path: Path) -> None:
    """The salvage marking leaves every pre-existing ledger byte identical.

    A stopped_stall fixture, a well-formed seed record in the ledger, and
    a pre-existing unit-level verdict row: then one marking harvest. After
    it, every snapshotted file is byte-identical, the only new files are
    the harvest record and akar's append lock, the pre-existing verdict
    rows survive verbatim as a strict prefix of the marked file, and the
    appended tail is exactly one season-level row carrying the mark.
    Green pre-graft by design (the close already appends); the directive
    seq 5 discipline the season must not weaken.
    """
    proj, root = _s62w2_proj(tmp_path)
    _s62w2_complete(tmp_path, root, S62W2_SID_C, "dead")

    seed_body = "seed note body: pre-existing bytes the marking must not touch\n"
    seed = root / "ledger" / "2026-09-16_seed-note.md"
    seed.write_text(
        "\n".join(
            [
                "# akar record: seed-note",
                "id: seed-note",
                "date: 2026-09-16",
                "title: seed note",
                seed_body,
                f"sha256: {hashlib.sha256(seed_body.encode('utf-8')).hexdigest()}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    verdicts = root / "runs" / S62W2_SID_C / "verdicts.jsonl"
    verdicts.write_text(
        json.dumps({"unit": "u1", "verdict": "PASS"}) + "\n", encoding="utf-8",
    )

    watched = [root / "ledger", root / "runs" / S62W2_SID_C]
    before = {
        path: path.read_bytes()
        for watched_dir in watched
        for path in sorted(watched_dir.rglob("*"))
        if path.is_file()
    }

    _s62w2_harvest(proj, S62W2_SID_C)

    after_paths = {
        path
        for watched_dir in watched
        for path in sorted(watched_dir.rglob("*"))
        if path.is_file()
    }
    for path, old in before.items():
        if path == verdicts:
            continue  # the marked file: its discipline is the prefix check below
        assert path.is_file() and path.read_bytes() == old, (
            f"the marking mutated pre-existing bytes: {path}"
        )
    fresh = after_paths - set(before)
    ledger = root / "ledger"
    for path in fresh:
        assert path.parent == ledger and (
            path.name == "append.lock" or path.name.endswith("-harvest.md")
        ), f"the marking created an unexpected file: {path}"
    new_records = [p for p in fresh if p.name.endswith("-harvest.md")]
    assert [p.name for p in new_records] == [f"2026-09-16_{S62W2_SID_C}-harvest.md"], (
        f"expected exactly the {S62W2_SID_C}-harvest record, got {new_records}"
    )

    after = verdicts.read_bytes()
    assert after.startswith(before[verdicts]), (
        "the marked verdicts file rewrote pre-existing bytes"
    )
    tail_rows = [
        json.loads(line)
        for line in after[len(before[verdicts]):].decode("utf-8").splitlines()
        if line.strip()
    ]
    assert len(tail_rows) == 1, f"the marking appended {len(tail_rows)} rows: {tail_rows}"
    assert tail_rows[0].get("season") == S62W2_SID_C, f"appended row: {tail_rows}"
    assert tail_rows[0].get("verdict") == "WIN", f"appended row: {tail_rows}"
    assert tail_rows[0].get("salvaged") is True, (
        f"the appended row carries no salvage mark: {tail_rows}"
    )
    title = _s62w2_title(_s62w2_harvest_record(root, S62W2_SID_C))
    assert "(salvaged)" in title, f"the marked close record title is unmarked: {title!r}"
    logger.info("pin 3 held: the marking wrote only new rows and records")
