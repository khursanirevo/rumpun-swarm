"""s66 w2 pins — spec-first pins for the kanban verb.

Spec-first pins for the `rumpun kanban` contract (directive seq 7 and the
seq 8 card-format addendum, .rumpun/ledger/directives.jsonl; ledger anchors
s65-harvest and audit-42). The verb does not exist yet: every pin here is
spec-first red against the current tree, and w1's cli.py landing must turn
them green at merge. Spec anchors, the measured red set, and fixture-shape
assumptions: .rumpun/runs/s66/w2/notes.md.

Contract these pins hold — `rumpun kanban` renders all four columns
(backlog, doing, need-human, done) derived only from the ledger, the runs
state, and the directives, and writes nothing (no new state file). The
backlog column names the audit record's armed candidates; the doing column
names the season whose persisted state says running; the done column counts
harvested seasons and carries their verdicts and salvage marks. A NEED HUMAN
card (directive seq 8) carries four plain sentences: what happened, what
needs doing, why it needs a human, and what happens if nobody acts. A fresh
campaign with no history renders empty columns and exits 0.

1. The four columns from a full fixture campaign: backlog naming an armed
   candidate, doing naming the running season, done counting the harvested
   seasons with verdicts and salvage marks.
2. The unset-cap NEED HUMAN card (audit-42's F6 gap) renders all four
   sentences, in directive order.
3. A fresh campaign renders empty columns, exits 0, and creates no new
   state file — the full file snapshot is byte-for-byte unchanged.

Red history (measured 2026-09-16; logs /tmp/s66w2-run*.log): all 3 pins red
in run 1, each red for the missing verb: `rumpun kanban` exits 2 (argparse
"invalid choice: 'kanban'") because cli.py has no kanban parser yet. Pin 2
additionally proves the shape contract is load-bearing: its sentence and
theme assertions sit behind the exit check, so the merge landing must turn
them green as a set. run 1: 3 failed, no errors, no fixture defects
(fixture lint, starts, audit, and hand-built done artifacts all held).

Grafting: drop this file into tests/ as the season's pins file. Helpers
carry the _s66w2_ prefix, so nothing collides with existing defs.
Fixture-shape assumptions the harness reconciles at merge: (a) column
headers render as LINES THAT START WITH the column name, case-insensitive
(backlog / doing / need[-_ ]human / done); (b) a column's region is the
text between its header line and the next column header line; (c) the
unset-cap card is the whole need-human region, exactly four sentences
ending in . ! or ? with no other card title line, themes in directive
order; (d) the done column counts its seasons in the header or body (the
digit 2 must appear); (e) the running season is named in the doing region
by its id; (f) the armed candidate is named by its trigger text
("exercise or trim phase execute"); (g) hand-built done artifacts use the
exact harvest.py shapes (verdicts.jsonl row + sha-sealed <sid>-harvest
ledger record; salvage via "salvaged": true and the "(salvaged)" record
title); (h) the running-season state.json uses the engine's own start
shape (engine.py: {"id", "status": "running", "started_at", "stall_s",
"budget_s", "spawned"} — the live s66 season state is that shape).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)

S66W2_TIMEOUT = 240  # bounds one CLI subprocess (the task bound)

# The fixture campaign's five seasons, one per kanban fact.
S66W2_DONE_WIN = "s650"  # real start, completed close, harvested WIN
S66W2_MID = "s651"  # real start, completed close, unharvested (audit fodder)
S66W2_SEED = "s652"  # unfilled seed: yaml drafted, no run state at all
S66W2_SALV = "s653"  # stopped_stall close, harvested LOSS with salvage mark
S66W2_RUN = "s654"  # the running season (the doing column)
S66W2_COMMIT = "a1b2c3d4e5" * 4  # 40-hex fixture close commit

S66W2_PC = (
    "  primary_change:\n"
    "    type: add\n"
    "    node: execute\n"
    '    baseline: "the campaign board is the season list, not a kanban view"\n'
    '    expected_band: "WIN if the kanban verb renders the four columns"\n'
    '    rollback: "git revert the s66 commits"\n'
    '    eval_window: "w2 pins"\n'
)

S66W2_SEASON = """\
id: {sid}
{parent}goal: "fixture season for the s66 kanban pins"
metric: "m"
mode: fight
methodology:
  approach: "stub close for the kanban fixture"
  evidence: []
{pc}  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
      reads: results.jsonl
writers:
  - name: w1
    route: stub
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [all_exited, {{stall_minutes: 0.1}}]
"""

# Directive seq 8 themes, in order: what happened, what needs doing, why it
# needs a human, what happens if nobody acts. Loose anchors; wording is w1's.
S66W2_THEMES: tuple[tuple[str, str], ...] = (
    (r"campaign_cost_cap|cost cap", "what happened"),
    (r"\bset\b", "what needs doing"),
    (r"human|operator|you\b", "why it needs a human"),
    (
        r"nobody|no one|without|until|stays? unset|not set|uncapped|"
        r"won't|will not|cannot|can't|blocks?",
        "what happens if nobody acts",
    ),
)


def _s66w2_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and in
    tests/ (post-graft): both sit under the repo root.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s66w2_campaign(tmp_path: Path, tag: str) -> tuple[Path, Path]:
    """One throwaway five-season campaign; (campaign root, proj dir).

    The only route is a stub that exits 0 instantly, so a start closes
    in one watcher cycle with no model quota and no network. Five yamls:
    s650 (seed), s651 (non-seed, parent s650), s652 (seed, never started —
    the unfilled seed), s653 (non-seed, parent s650), s654 (seed).
    """
    root = tmp_path / tag / "proj" / ".rumpun"
    proj = root.parent
    for sub in ("seasons", "ledger", "runs", "prompts/dev"):
        (root / sub).mkdir(parents=True)
    (root / "prompts" / "dev" / "dummy.md").write_text(
        "prompt body\n", encoding="utf-8",
    )
    (root / "rumpun.yaml").write_text(
        "autonomy:\n"
        "  stage: manual\n"
        "  invariants: [goal_immutable, budget_cap, falsify_required]\n"
        "routes:\n"
        "  stub: 'true'\n",
        encoding="utf-8",
    )
    shapes = {
        S66W2_DONE_WIN: "",
        S66W2_MID: f"parent: {S66W2_DONE_WIN}\n",
        S66W2_SEED: "",
        S66W2_SALV: f"parent: {S66W2_DONE_WIN}\n",
        S66W2_RUN: "",
    }
    for sid, parent in shapes.items():
        (root / "seasons" / f"{sid}.yaml").write_text(
            S66W2_SEASON.format(
                sid=sid, parent=parent,
                pc="" if not parent else S66W2_PC,
            ),
            encoding="utf-8",
        )
    return root, proj


def _s66w2_cli(
    tmp_path: Path, *argv: str, cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """One bounded rumpun CLI subprocess (240s cap); PYTHONPATH pins repo src.

    cwd points at the fixture proj dir when the verb resolves the campaign
    from cwd (kanban); the default tmp_path keeps fixture-internal calls
    (lint, season start) outside the campaign when possible.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_s66w2_repo() / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "rumpun", *argv], cwd=str(cwd) if cwd else str(tmp_path),
        capture_output=True, text=True, timeout=S66W2_TIMEOUT, check=False,
    )


def _s66w2_lint_ok(tmp_path: Path, season: Path) -> None:
    """Fixture sanity: the season lints clean BEFORE any kanban step.

    A lint refusal would exit nonzero without rendering columns, and an
    exit-0 render pin would red for the wrong reason; this isolates
    fixture validity from verb behavior.
    """
    proc = _s66w2_cli(tmp_path, "lint", str(season))
    assert proc.returncode == 0, (
        f"fixture defect: {season.name} does not lint clean; the pin would "
        f"red for the wrong reason\nstderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )


def _s66w2_completed(tmp_path: Path, root: Path, sid: str) -> None:
    """A start that must succeed AND persist status completed.

    The rc assert alone could pass on a refusal-shaped success; the
    persisted state names the real terminal status.
    """
    proc = _s66w2_cli(tmp_path, "season", "start", str(root / "seasons" / f"{sid}.yaml"))
    assert proc.returncode == 0, (
        f"season start exit {proc.returncode}; the fixture campaign must start\n"
        f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )
    state_path = root / "runs" / sid / "_season" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state.get("status") == "completed", (
        f"season {sid} persisted {state.get('status')!r}, not completed; "
        f"stderr:\n{proc.stderr}"
    )


def _s66w2_akar(path: Path, record_id: str, date: str, title: str, body: list[str]) -> None:
    """One sha-sealed ledger record in the real corpus shape.

    Four header lines, the body, then a final sha256 line digesting the
    body exactly (the akar.append_record layout; the s65 pins validated
    this helper at their merge). Nothing here writes outside the fixture.
    """
    header = [
        f"# akar record: {record_id}",
        f"id: {record_id}",
        f"date: {date}",
        f"title: {title}",
    ]
    digest = hashlib.sha256("\n".join(body).encode("utf-8")).hexdigest()
    path.write_text("\n".join(header + body + [f"sha256: {digest}"]) + "\n", encoding="utf-8")


def _s66w2_done(root: Path, sid: str, verdict: str, salvaged: bool, status: str) -> None:
    """Hand-write one done-column season in the exact harvest.py shapes.

    The real 'rumpun harvest' verb is never called: it also spawns the s55
    checker against the REPO's own ledger (cmd_harvest -> _run_check), so a
    fixture close would append a check record into the live campaign
    ledger. Instead the pin writes the two artifacts the verb itself would
    write, byte-shape faithful: the verdicts.jsonl season row (metric/band/
    observed/implies plus "salvaged": true for a stopped_* close) and the
    sha-sealed <sid>-harvest record (title carries "(salvaged)" for a
    salvage). state.json gets the engine's terminal shape so the campaign
    is internally consistent.
    """
    date = time.strftime("%Y-%m-%d")
    started = time.time() - 60.0
    runs = root / "runs" / sid
    (runs / "_season").mkdir(parents=True, exist_ok=True)
    state = {
        "id": sid, "status": status, "started_at": started,
        "stall_s": 0.1, "budget_s": 2400.0, "spawned": {},
        "ended_at": started + 6.0, "agents": {},
    }
    (runs / "_season" / "state.json").write_text(
        json.dumps(state, indent=2) + "\n", encoding="utf-8",
    )
    implies = "fixture close for the s66 kanban pins"
    row: dict[str, object] = {
        "season": sid, "verdict": verdict, "metric": "m", "band": "",
        "observed": "", "implies": implies,
    }
    if salvaged:
        row["salvaged"] = True
    with (runs / "verdicts.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    body = [
        f"season {sid}: {status}",
        "duration: 6s",
        "",
        "| agent | route | state | exit_code | seconds |",
        "|---|---|---|---|---|",
        "| w1 | stub | exited | 0 | 1.0 |",
        "",
        f"verdict: {verdict}",
        f"implies: {implies}",
    ]
    title = f"season {sid} harvest" + (" (salvaged)" if salvaged else "")
    _s66w2_akar(
        root / "ledger" / f"{date}_{sid}-harvest.md", f"{sid}-harvest", date, title, body,
    )


def _s66w2_running(root: Path, sid: str) -> None:
    """Hand-write the running season's state in the engine's own start shape.

    The live s66 season state (.rumpun/runs/s66/_season/state.json) is that
    shape: {"id", "status": "running", "started_at", "stall_s", "budget_s",
    "spawned"} with no agents block until finalize. A real background start
    would race kanban (the dual-start race the s21 season already paid
    for), so the fixture persists the state directly.
    """
    runs = root / "runs" / sid / "_season"
    runs.mkdir(parents=True, exist_ok=True)
    state = {
        "id": sid, "status": "running", "started_at": time.time() - 30.0,
        "stall_s": 900.0, "budget_s": 2400.0, "spawned": {},
    }
    (runs / "state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _s66w2_audit(tmp_path: Path, proj: Path) -> None:
    """Arm a real candidate: 'rumpun audit --last 10' in the fixture.

    Two completed stub seasons with a declared execute->results.jsonl phase
    arm the F1 trigger ("exercise or trim phase execute"); the record and
    its candidate lines land in the fixture ledger in the real audit-N
    shape. No --corpus, so no runner subprocess.
    """
    for stale in sorted(proj.glob(".rumpun/runs/s*/results.jsonl")):
        stale.unlink()  # the F1 gap world: the artifact was never written
    proc = _s66w2_cli(tmp_path, "audit", "--last", "10", cwd=proj)
    assert proc.returncode == 0, (
        f"fixture defect: 'rumpun audit' failed; the backlog pin would red "
        f"for the wrong reason\nstderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )


def _s66w2_snapshot(root: Path) -> set[str]:
    """Relative posix paths of every file under the campaign root."""
    return {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file()
    }


def _s66w2_columns(out: str) -> dict[str, str]:
    """Split the kanban output into column regions keyed by column name.

    A column header is a LINE THAT STARTS WITH the column name
    (case-insensitive): backlog, doing, need[-_ ]?human, done. A column's
    region is the text from just after its header line to the next column
    header line (or end of output).
    """
    pats = {
        "backlog": re.compile(r"^backlog\b", re.IGNORECASE),
        "doing": re.compile(r"^doing\b", re.IGNORECASE),
        "need-human": re.compile(r"^need[-_ ]?human\b", re.IGNORECASE),
        "done": re.compile(r"^done\b", re.IGNORECASE),
    }
    lines = out.splitlines()
    found: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        for name, pat in pats.items():
            if pat.search(line):
                found.append((idx, name))
                break
    regions: dict[str, str] = {}
    for pos, (idx, name) in enumerate(found):
        stop = found[pos + 1][0] if pos + 1 < len(found) else len(lines)
        regions[name] = "\n".join(lines[idx + 1 : stop])
    return regions


def _s66w2_sentences(card: str) -> list[str]:
    """Sentence split of the card: split after terminal punctuation."""
    return [s for s in re.split(r"(?<=[.!?])\s+", card.strip()) if s]


# --- pin 1: the four columns ---------------------------------------------------------


def test_s66w2_kanban_renders_all_four_columns(tmp_path: Path) -> None:
    """`rumpun kanban` renders backlog/doing/need-human/done from the campaign.

    The fixture closes s650 and s651 through the real engine (the stub
    writer exits 0), hand-writes the done-column artifacts for s650 (WIN)
    and s653 (LOSS, salvage mark) in the exact harvest shapes, persists
    s654's running state in the engine's own start shape, and arms a real
    candidate through 'rumpun audit'. Kanban must render all four column
    headers, name the armed candidate in backlog, name s654 in doing, and
    count both harvested seasons with verdicts and the salvage mark in
    done. On a tree without the verb the call exits 2 with no columns —
    directive seq 7's gap verbatim; this pin is the red the landing must
    turn green. The campaign file snapshot is taken before the render and
    must be unchanged after it: the verb derives everything from the
    ledger, runs state, and directives and writes nothing.
    """
    root, proj = _s66w2_campaign(tmp_path, "four-columns")
    _s66w2_lint_ok(tmp_path, root / "seasons" / f"{S66W2_MID}.yaml")
    _s66w2_completed(tmp_path, root, S66W2_DONE_WIN)
    _s66w2_completed(tmp_path, root, S66W2_MID)
    _s66w2_done(root, S66W2_DONE_WIN, "WIN", salvaged=False, status="completed")
    _s66w2_done(root, S66W2_SALV, "LOSS", salvaged=True, status="stopped_stall")
    _s66w2_running(root, S66W2_RUN)
    _s66w2_audit(tmp_path, proj)
    before = _s66w2_snapshot(root)
    proc = _s66w2_cli(tmp_path, "kanban", cwd=proj)
    combined = proc.stdout + "\n" + proc.stderr
    assert proc.returncode == 0, (
        f"rumpun kanban exit {proc.returncode}; the verb must render the four "
        f"columns from the fixture campaign. output:\n{combined}"
    )
    regions = _s66w2_columns(proc.stdout)
    for name in ("backlog", "doing", "need-human", "done"):
        assert name in regions, (
            f"kanban output is missing the {name} column; output:\n{proc.stdout}"
        )
    assert "exercise or trim phase execute" in regions["backlog"], (
        f"the backlog column must name the armed candidate "
        f"'exercise or trim phase execute'; regions:\n{regions}"
    )
    assert S66W2_RUN in regions["doing"], (
        f"the doing column must name the running season {S66W2_RUN}; "
        f"regions:\n{regions}"
    )
    done = regions["done"]
    for token in (S66W2_DONE_WIN, S66W2_SALV, "WIN", "LOSS", "salvaged"):
        assert token in done, (
            f"the done column must carry verdicts and the salvage mark "
            f"(missing {token!r}); regions:\n{regions}"
        )
    assert re.search(r"\b2\b", done), (
        f"the done column must count its seasons (2 harvested); regions:\n{regions}"
    )
    after = _s66w2_snapshot(root)
    assert after == before, (
        f"kanban wrote to the campaign (no new state file: directive seq 7); "
        f"delta: {sorted(after ^ before)}"
    )
    logger.info(
        "pin 1 held: four columns rendered; candidate in backlog, %s in doing, "
        "done counted 2 harvested with the salvage mark; campaign unchanged",
        S66W2_RUN,
    )


# --- pin 2: the NEED HUMAN card format ----------------------------------------------


def test_s66w2_need_human_card_carries_four_sentences(tmp_path: Path) -> None:
    """The unset-cap NEED HUMAN card renders all four sentences (seq 8).

    The fixture closes s650 (WIN) so done is populated, leaves the budget
    block out of rumpun.yaml so campaign_cost_cap is unset (audit-42's F6
    finding: "campaign_cost_cap unset since campaign start (P9) — operator
    sets the number; the tool only flags"), and runs kanban. The need-human
    region must name the unset cap and carry exactly four sentences — what
    happened, what needs doing, why it needs a human, what happens if
    nobody acts — anchored in directive order. "no card ships without
    them": a card with fewer (or looser) sentences reds this pin.
    """
    root, proj = _s66w2_campaign(tmp_path, "unset-cap-card")
    _s66w2_lint_ok(tmp_path, root / "seasons" / f"{S66W2_MID}.yaml")
    _s66w2_completed(tmp_path, root, S66W2_DONE_WIN)
    _s66w2_done(root, S66W2_DONE_WIN, "WIN", salvaged=False, status="completed")
    proc = _s66w2_cli(tmp_path, "kanban", cwd=proj)
    combined = proc.stdout + "\n" + proc.stderr
    assert proc.returncode == 0, (
        f"rumpun kanban exit {proc.returncode}; output:\n{combined}"
    )
    regions = _s66w2_columns(proc.stdout)
    assert "need-human" in regions, (
        f"kanban output is missing the need-human column; output:\n{proc.stdout}"
    )
    card = regions["need-human"]
    assert re.search(r"campaign_cost_cap|cost cap", card, re.IGNORECASE), (
        f"the unset-cap card must name the unset cap; card:\n{card}"
    )
    sentences = _s66w2_sentences(card)
    assert len(sentences) == 4, (
        f"the NEED HUMAN card carries exactly four sentences (directive seq 8), "
        f"got {len(sentences)}: {sentences}"
    )
    cursor = 0
    for pattern, theme in S66W2_THEMES:
        match = re.search(pattern, card[cursor:], re.IGNORECASE)
        assert match, (
            f"the unset-cap card is missing the {theme!r} sentence theme "
            f"(anchor {pattern!r}); card:\n{card}"
        )
        cursor += match.start()
    logger.info("pin 2 held: the unset-cap NEED HUMAN card carried all four sentences")


# --- pin 3: fresh campaign -----------------------------------------------------------


def test_s66w2_fresh_campaign_renders_empty_and_writes_nothing(tmp_path: Path) -> Path:
    """A fresh campaign renders empty columns, exits 0, and writes nothing.

    The fixture is an initialized campaign with no seasons, no ledger, no
    runs: kanban must render all four column headers with no season ids,
    no candidate text, no salvage marks, and exit 0. The full campaign
    file snapshot must be unchanged after the render — the verb derives
    everything from the ledger, runs state, and directives; there is no
    new state file (directive seq 7).
    """
    root = tmp_path / "fresh" / "proj" / ".rumpun"
    proj = root.parent
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        "autonomy:\n"
        "  stage: manual\n"
        "  invariants: [goal_immutable, budget_cap, falsify_required]\n"
        "routes:\n"
        "  stub: 'true'\n",
        encoding="utf-8",
    )
    before = _s66w2_snapshot(root)
    proc = _s66w2_cli(tmp_path, "kanban", cwd=proj)
    combined = proc.stdout + "\n" + proc.stderr
    assert proc.returncode == 0, (
        f"rumpun kanban exit {proc.returncode} on a fresh campaign; "
        f"empty columns and exit 0 is the contract. output:\n{combined}"
    )
    regions = _s66w2_columns(proc.stdout)
    for name in ("backlog", "doing", "need-human", "done"):
        assert name in regions, (
            f"kanban output is missing the {name} column; output:\n{proc.stdout}"
        )
    board_lines = {
        line
        for line in proc.stdout.splitlines()
        if re.search(r"\[https://github\.com/", line)
    }
    local_output = "\n".join(
        line for line in proc.stdout.splitlines() if line not in board_lines
    )
    assert not re.search(r"\bs\d+\b", local_output), (
        f"a fresh campaign renders no LOCAL season ids; board-sourced cards"
        f" may name other machines' seasons (the s69 seam);"
        f" output:\n{proc.stdout}"
    )
    assert "salvaged" not in proc.stdout.lower(), (
        f"a fresh campaign renders no salvage marks; output:\n{proc.stdout}"
    )
    after = _s66w2_snapshot(root)
    assert after == before, (
        f"kanban wrote a new state file into the fresh campaign "
        f"(directive seq 7: no new state file); delta: {sorted(after ^ before)}"
    )
    logger.info("pin 3 held: fresh campaign rendered empty columns and wrote nothing")
    return root


# --- why pin 3 returns root ----------------------------------------------------------
# test_s66w2_fresh_campaign_renders_empty_and_writes_nothing returns the
# campaign root for harness tooling (the merge check can diff the snapshot
# itself); pytest ignores the return value.
