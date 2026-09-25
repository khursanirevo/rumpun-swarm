"""s89 w2 pins — the epic rollup's arithmetic as a pinned contract.

Spec source: the s89 w2 brief (.rumpun/runs/s89/w2/prompt.md), w1's
hand-verified arithmetic (.rumpun/runs/s89/w1/notes.md — the s85 split
rule: the two views sum to the whole ledger, 71 WIN + 9 LOSS + 7 other
plus one no-state season = 88), and the real split (.rumpun/epics.yaml:
board-arc s69-s88, campaign s1-s68, disjoint, s1 the one stateless
member). These pins turn that hand-checked arithmetic into a standing
contract: the per-epic counts always partition the whole ledger — no
verdict counted twice, none vanished.

Contract these pins hold — `rumpun epics` over .rumpun/epics.yaml
(src/rumpun/epics.py render, gated by lint_epics in cli.cmd_epics):

1. The sum invariant: over a fixture campaign whose two epics partition
   the seasons, board-arc's counts + campaign's counts equal the
   whole-ledger counts (the s64 composer convention: every season in
   exactly one slot — WIN, LOSS, other, or the no-state mark), for the
   base partition and for every single-season move between the epics.
   Each epic's counts also equal the independently computed fixture
   truth, so drift in either view fails, not just the sum.
2. The no-double-membership + no-vanish pair: a season declared in two
   epics refuses nonzero naming the season and both epics (the guard:
   it would sit in two sums); a member with no run state is marked
   `(no state: s1)` on its epic's line, excluded from the counts,
   never guessed.
3. The extension conserves: board-arc starting as a one-season stub and
   campaign holding the rest, extending board-arc with four seasons
   (the w1 landing shape: s85-s88 joined board-arc) keeps the two-view
   sum equal to the same whole, and the deltas are exact negatives —
   board-arc gains exactly what campaign loses: (2 WIN, 1 LOSS,
   1 other).

Every pin builds its own miniature campaign under pytest tmp_path and
runs the verb as a bounded subprocess (S89W2_TIMEOUT = 120s), cwd inside
the campaign, the tree under test's src/ first on PYTHONPATH (the s58
w2 pattern). No pin mutates the real repo, ledger, or epics.yaml; the
fixture verdict rows are hand-built (no harvest verb in a fixture).
The fixture-truth counters (_s89w2_counts_for / _s89w2_whole_counts)
are computed from the fixture constants only, never from the code
under test. Measured results: .rumpun/runs/s89/w2/notes.md.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

S89W2_TIMEOUT = 120  # the spec bound for one verb run

# The fixture ledger mirrors the real split compactly: s1 is the
# stateless member (the real s1 shape); s83 has run state and no
# verdict row (the honest `other`); s84-s86 WIN, s87 LOSS, s88 NEUTRAL
# (NEUTRAL falls into `other`). Whole: 3 WIN / 1 LOSS / 2 other, s1
# marked, 6 counted of 7 seasons.
S89W2_ALL_IDS = ("s1", "s83", "s84", "s85", "s86", "s87", "s88")
S89W2_NO_STATE = ("s1",)
S89W2_VERDICTS = {
    "s84": "WIN",
    "s85": "WIN",
    "s86": "WIN",
    "s87": "LOSS",
    "s88": "NEUTRAL",
}

# The base partition mirrors the real split: the late block in
# board-arc, the early block plus the stateless s1 in campaign.
S89W2_BASE_BOARD = ("s84", "s85", "s86", "s87", "s88")
S89W2_BASE_CAMP = ("s1", "s83")

S89W2_COUNT_RE = re.compile(r"(\d+) WIN / (\d+) LOSS / (\d+) other")


def _s89w2_repo() -> Path:
    """The repo root: first ancestor of this file holding pyproject.toml."""
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise AssertionError("no pyproject.toml above the pins file")


def _s89w2_env() -> dict[str, str]:
    """The subprocess env: the tree under test's src/ first on PYTHONPATH."""
    env = dict(os.environ)
    src = str(_s89w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s89w2_run(cwd: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    """One bounded `python -m rumpun <argv>` run with cwd inside the campaign."""
    try:
        return subprocess.run(
            [sys.executable, "-m", "rumpun", *argv],
            cwd=str(cwd),
            env=_s89w2_env(),
            capture_output=True,
            text=True,
            timeout=S89W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"rumpun {' '.join(argv)} exceeded {S89W2_TIMEOUT}s"
        raise AssertionError(msg) from exc


def _s89w2_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _s89w2_epics_doc(board: Iterable[str], camp: Iterable[str]) -> str:
    """Hand-written declaration text for the (board-arc, campaign) partition."""
    lines = [
        "board-arc:",
        "  title: the board arc",
        "  goal: fixture board goal",
        "  seasons:",
    ]
    lines += [f"  - {sid}" for sid in board]
    lines += [
        "campaign:",
        "  title: campaign",
        "  goal: fixture campaign goal",
        "  seasons:",
    ]
    lines += [f"  - {sid}" for sid in camp]
    return "\n".join(lines) + "\n"


def _s89w2_campaign(root: Path, epics_text: str | None) -> Path:
    """The s89 fixture campaign: 7 seasons, verdicts per the constants,
    run state for every counted member, s1 with nothing on disk."""
    rump = root / ".rumpun"
    _s89w2_write(rump / "rumpun.yaml", "campaign: s89w2-epics-fixture\n")
    for sid in S89W2_ALL_IDS:
        _s89w2_write(rump / "seasons" / f"{sid}.yaml", f"id: {sid}\n")
    stateful = [sid for sid in S89W2_ALL_IDS if sid not in S89W2_NO_STATE]
    for sid in stateful:
        state = {
            "id": sid,
            "status": "completed",
            "started_at": 1789500000.0,
            "ended_at": 1789500060.0,
            "agents": {},
        }
        _s89w2_write(
            rump / "runs" / sid / "_season" / "state.json",
            json.dumps(state, indent=2) + "\n",
        )
    for sid, verdict in S89W2_VERDICTS.items():
        row = {
            "season": sid,
            "verdict": verdict,
            "metric": "",
            "band": "",
            "observed": "",
            "implies": "s89w2 fixture row",
        }
        _s89w2_write(rump / "runs" / sid / "verdicts.jsonl", json.dumps(row) + "\n")
    _s89w2_write(
        rump / "ledger" / "2026-09-17_s84-harvest.md",
        "# akar record: s84-harvest\nid: s84-harvest\ndate: 2026-09-17\n"
        "title: season s84 harvest\nverdict: WIN\nimplies: fixture row\n",
    )
    directive = {"from": "operator", "seq": 0, "status": "pending", "text": "fixture"}
    _s89w2_write(rump / "ledger" / "directives.jsonl", json.dumps(directive) + "\n")
    _s89w2_write(rump / "ledger" / "append.lock", "")
    if epics_text is not None:
        _s89w2_write(rump / "epics.yaml", epics_text)
    return root


def _s89w2_counts_for(members: Iterable[str]) -> tuple[int, int, int]:
    """Fixture-truth counts: WIN/LOSS exact; NEUTRAL and state-without-
    verdict into `other`; stateless members excluded (they are marked)."""
    wins = losses = others = 0
    for sid in members:
        if sid in S89W2_NO_STATE:
            continue
        verdict = S89W2_VERDICTS.get(sid)
        if verdict == "WIN":
            wins += 1
        elif verdict == "LOSS":
            losses += 1
        else:
            others += 1
    return (wins, losses, others)


def _s89w2_whole_counts() -> tuple[int, int, int]:
    """The whole-ledger counts over every fixture season."""
    return _s89w2_counts_for(S89W2_ALL_IDS)


def _s89w2_add(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, ...]:
    """Componentwise tuple sum (deltas pass negatives)."""
    return tuple(x + y for x, y in zip(a, b, strict=True))


def _s89w2_epic_line(stdout: str, epic_id: str) -> str:
    """The single rendered stdout line carrying epic_id."""
    hits = [ln for ln in stdout.splitlines() if re.search(rf"\b{epic_id}\b", ln)]
    assert len(hits) == 1, (
        f"expected exactly one rendered line for {epic_id}, got {len(hits)}:\n{stdout}"
    )
    return hits[0]


def _s89w2_parse_counts(line: str) -> tuple[int, int, int]:
    """The (WIN, LOSS, other) triple parsed off one rendered epic line."""
    m = S89W2_COUNT_RE.search(line)
    assert m, f"no count triple in the rendered line:\n{line}"
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))

S89W2_WHOLE_COUNTED = 6  # every counted member sits in exactly one epic

_MOVES = [None, *S89W2_ALL_IDS]
_MOVE_IDS = ["base", *S89W2_ALL_IDS]


# --- pin 1: the sum invariant over every fixture permutation ---------------


@pytest.mark.parametrize("mover", _MOVES, ids=_MOVE_IDS)
def test_s89w2_sum_invariant_over_fixture_permutations(
    mover: str | None, tmp_path: Any
) -> None:
    """The views sum to the whole for the base partition and for every
    single-season move between the epics: each epic's counts equal the
    fixture truth, board-arc + campaign equal the whole-ledger counts
    (3 WIN / 1 LOSS / 2 other), the counted total conserves at 6, and
    the stateless s1 is marked on its epic's line wherever it sits.
    """
    board = [sid for sid in S89W2_BASE_BOARD if sid != mover]
    camp = [sid for sid in S89W2_BASE_CAMP if sid != mover]
    if mover is not None:
        (camp if mover in S89W2_BASE_BOARD else board).append(mover)
    root = _s89w2_campaign(tmp_path / "fx", _s89w2_epics_doc(board, camp))
    proc = _s89w2_run(root, "epics")
    streams = proc.stdout + proc.stderr
    assert proc.returncode == 0, streams
    rendered = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    # s110: the render grew one indented basis line per member under each
    # row (2 rows + one line per fixture season); the rows and their counts
    # are pinned exactly as before.
    assert len(rendered) == 2 + len(S89W2_ALL_IDS), proc.stdout
    line_board = _s89w2_epic_line(proc.stdout, "board-arc")
    line_camp = _s89w2_epic_line(proc.stdout, "campaign")
    got_board = _s89w2_parse_counts(line_board)
    got_camp = _s89w2_parse_counts(line_camp)
    want_board = _s89w2_counts_for(board)
    want_camp = _s89w2_counts_for(camp)
    assert got_board == want_board, f"board-arc counts drifted:\n{line_board}"
    assert got_camp == want_camp, f"campaign counts drifted:\n{line_camp}"
    assert _s89w2_add(got_board, got_camp) == _s89w2_whole_counts()
    assert sum(got_board) + sum(got_camp) == S89W2_WHOLE_COUNTED
    # the stateless member: marked where it sits, counted nowhere
    holder_is_board = "s1" in board
    holder_line = line_board if holder_is_board else line_camp
    other_line = line_camp if holder_is_board else line_board
    assert "(no state: s1)" in holder_line, holder_line
    assert "no state" not in other_line, other_line


# --- pin 2: the no-double-membership + no-vanish pair -----------------------


def test_s89w2_double_membership_lints_out(tmp_path: Any) -> None:
    """A season declared in two epics refuses nonzero, naming the season
    and both epics — the guard that keeps it out of two sums."""
    camp = [*S89W2_BASE_CAMP, "s88"]
    root = _s89w2_campaign(tmp_path / "fx", _s89w2_epics_doc(S89W2_BASE_BOARD, camp))
    proc = _s89w2_run(root, "epics")
    streams = proc.stdout + proc.stderr
    assert proc.returncode != 0, streams
    for token in ("s88", "board-arc", "campaign"):
        assert token in streams, f"the lint refusal must name {token}:\n{streams}"


def test_s89w2_member_without_run_state_is_marked_not_counted(tmp_path: Any) -> None:
    """The `(no state: s1)` shape: the stateless member is named on its
    epic's line, excluded from the counts, never guessed. The campaign
    line reads exactly: span s1-s83, 0 WIN / 0 LOSS / 1 other (s83 has
    run state and no verdict row — the honest `other`), then the mark;
    board-arc counts its five members with no mark.
    """
    root = _s89w2_campaign(
        tmp_path / "fx", _s89w2_epics_doc(S89W2_BASE_BOARD, S89W2_BASE_CAMP)
    )
    proc = _s89w2_run(root, "epics")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    line_camp = _s89w2_epic_line(proc.stdout, "campaign")
    assert re.search(r"\bs1-s83\b", line_camp), line_camp
    assert re.search(r"(?<![0-9])0 WIN / 0 LOSS / 1 other\b", line_camp), line_camp
    assert line_camp.rstrip().endswith("(no state: s1)"), line_camp
    line_board = _s89w2_epic_line(proc.stdout, "board-arc")
    assert re.search(r"(?<![0-9])3 WIN / 1 LOSS / 1 other\b", line_board), line_board
    assert "no state" not in line_board, line_board


# --- pin 3: the extension conserves -----------------------------------------


def test_s89w2_extension_preserves_the_sum(tmp_path: Any) -> None:
    """The w1 landing as a fixture: board-arc starts as the s84 stub and
    campaign holds the other six members; extending board-arc with
    s85-s88 (four seasons move) keeps the two-view sum equal to the
    same whole, and the deltas are exact negatives — board-arc gains
    exactly what campaign loses: (2 WIN, 1 LOSS, 1 other), the s85-s88
    carry. The board-arc span widens s84 to s84-s88; s1 stays marked.
    """
    pre_board = ("s84",)
    pre_camp = ("s1", "s83", "s85", "s86", "s87", "s88")
    pre_root = _s89w2_campaign(
        tmp_path / "pre", _s89w2_epics_doc(pre_board, pre_camp)
    )
    pre = _s89w2_run(pre_root, "epics")
    assert pre.returncode == 0, pre.stdout + pre.stderr
    post_root = _s89w2_campaign(
        tmp_path / "post", _s89w2_epics_doc(S89W2_BASE_BOARD, S89W2_BASE_CAMP)
    )
    post = _s89w2_run(post_root, "epics")
    assert post.returncode == 0, post.stdout + post.stderr

    pre_board_counts = _s89w2_parse_counts(_s89w2_epic_line(pre.stdout, "board-arc"))
    pre_camp_counts = _s89w2_parse_counts(_s89w2_epic_line(pre.stdout, "campaign"))
    post_board_counts = _s89w2_parse_counts(_s89w2_epic_line(post.stdout, "board-arc"))
    post_camp_counts = _s89w2_parse_counts(_s89w2_epic_line(post.stdout, "campaign"))

    assert pre_board_counts == (1, 0, 0), pre.stdout
    assert pre_camp_counts == (2, 1, 2), pre.stdout
    assert post_board_counts == (3, 1, 1), post.stdout
    assert post_camp_counts == (0, 0, 1), post.stdout
    assert _s89w2_add(pre_board_counts, pre_camp_counts) == _s89w2_whole_counts()
    assert _s89w2_add(post_board_counts, post_camp_counts) == _s89w2_whole_counts()
    carry = _s89w2_add(post_board_counts, tuple(-x for x in pre_board_counts))
    lost = _s89w2_add(pre_camp_counts, tuple(-x for x in post_camp_counts))
    assert carry == lost == (2, 1, 1)
    assert re.search(r"\bs84\b", _s89w2_epic_line(pre.stdout, "board-arc"))
    assert re.search(r"\bs84-s88\b", _s89w2_epic_line(post.stdout, "board-arc"))
    assert "(no state: s1)" in _s89w2_epic_line(pre.stdout, "campaign")
    assert "(no state: s1)" in _s89w2_epic_line(post.stdout, "campaign")
