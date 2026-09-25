"""s119 w2 pins — the board mirrors the ledger verdicts on demand.

Spec source: .rumpun/runs/s119/w2/prompt.md (the s119 w2 brief). The
board IS the backlog; the ledger holds the verdicts; one verb mirrors
the LOCAL ledger onto the board cards: a new card for a season with no
card, an updated body for a drifted card, nothing invented, idempotent
(a second run changes nothing).

Offline: the pins run the pure mirror logic over fixture verdicts --
ledger_truth, mirror_card_body, mirror_plan, mirror_sync with injected
seams (trail_fn, run) -- and the CLI wiring with monkeypatched module
names (the s74 w2 discipline). No gh call anywhere in this file.

Contract these pins hold -- src/rumpun/board.py + the cli wiring:

1. ledger_truth(root): {sid: (verdict, basis)} for every local season
   with a verdicts.jsonl row naming it -- the epics rollup's two
   sources exactly: the verdict is the LAST row naming the season
   (epics.season_verdict), the basis the harvest record's seal mark
   (epics._record_basis: '<sid>-harvest@<sha8>', the honest absence
   mark when nothing sealed). A season whose verdict file holds no row
   naming it is absent (nothing invented). A corrupt verdict file
   raises (a real read error, never a silent skip).
2. mirror_card_body: deterministic bytes -- marker, verdict, basis.
3. Card identity: a card's first `season: <sid>` line claims it; no
   marker, no claim. A foreign card -- unclaimed, or claiming a season
   the local truth holds no verdict for -- never plans: the s66
   lesson, the sync mirrors the LOCAL ledger and never censors.
4. mirror_plan: create for no card, update (the live issue number)
   for a drifted body, NOTHING for a matching body; duplicate markers
   first-wins in board order.
5. mirror_sync --dry-run: renders the plan, mutates nothing.
6. mirror_sync live: create -> item-add (the url read off the create
   stdout) -> edit --body, in plan order, through ONE seam; a failing
   action propagates (honest partial apply).
7. Idempotence end to end (pure): apply the plan to fixture cards,
   re-plan -> empty.
8. The CLI surface: `rumpun board --mirror [--dry-run]` prints the
   render and exits 0; the positional snapshot form keeps parsing.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

logger = logging.getLogger(__name__)

S119W2_URL_NEW = "https://github.com/khursanirevo/rumpun/issues/950"


def _s119w2_board_module():
    """Import rumpun.board; fail naming the spec reason when unlanded."""
    try:
        from rumpun import board as board_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/board.py missing/unimportable: {exc}")
    return board_module


def _s119w2_root(tmp_path: Path) -> Path:
    """A fresh .rumpun root: rumpun.yaml, empty ledger, runs, seasons."""
    campaign = tmp_path / "s119w2proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        "autonomy:\n  stage: manual\n", encoding="utf-8"
    )
    return root


def _s119w2_sealed_harvest(root: Path, sid: str) -> Path:
    """Append the <sid>-harvest record through akar itself; the seal is real."""
    from rumpun import akar

    return akar.append_record(
        root,
        f"{sid}-harvest",
        f"season {sid} harvest",
        f"season {sid}: completed\nverdict: WIN\n",
    )


def _s119w2_verdicts(root: Path, sid: str, *rows: str) -> Path:
    """Write runs/<sid>/verdicts.jsonl with the fixture rows verbatim."""
    path = root / "runs" / sid / "verdicts.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(row + "\n" for row in rows), encoding="utf-8")
    return path


def _s119w2_card(number: int, body: str) -> dict[str, Any]:
    """One issue_trail row: number, state, body (the s76 parser shape)."""
    return {"number": number, "state": "OPEN", "body": body}


def _s119w2_expected_body(sid: str, verdict: str, basis: str) -> str:
    """The expected card body, constructed inline (builder-independent)."""
    return f"season: {sid}\nverdict: {verdict}\nbasis: {basis}"


def _s119w2_tree_bytes(root: Path) -> dict[str, bytes]:
    """Every file under root as {relative path: bytes}, for write-nothing pins."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_s119w2_ledger_truth_reads_the_epics_sources(tmp_path: Path) -> None:
    """Truth = the epics sources exactly: last row naming the sid wins,
    the basis is the harvest record's real sha8 seal, a file with no
    row naming its season is absent, no harvest is the honest mark."""
    board = _s119w2_board_module()
    root = _s119w2_root(tmp_path)
    _s119w2_sealed_harvest(root, "s119f")
    _s119w2_verdicts(
        root,
        "s119f",
        '{"season": "s118", "verdict": "WIN"}',
        '{"season": "s119f", "verdict": "WIN"}',
        '{"season": "s119f", "verdict": "LOSS"}',
    )
    truth = board.ledger_truth(root)
    assert set(truth) == {"s119f"}, f"truth keys: {sorted(truth)!r}"
    verdict, basis = truth["s119f"]
    assert verdict == "LOSS", "the last row naming the season wins"
    assert basis.startswith("s119f-harvest@"), f"basis shape: {basis!r}"
    assert len(basis) == len("s119f-harvest@") + 8, "the sha8 seal prefix"
    # Verdict but no harvest record: the honest absence mark.
    _s119w2_verdicts(root, "s119g", '{"season": "s119g", "verdict": "WIN"}')
    # A verdict file whose rows name another season: its sid is absent.
    _s119w2_verdicts(root, "s120g", '{"season": "s119f", "verdict": "WIN"}')
    # A runs dir with no verdicts.jsonl: the glob never sees it.
    (root / "runs" / "s121h").mkdir()
    truth = board.ledger_truth(root)
    assert set(truth) == {"s119f", "s119g"}, f"truth keys: {sorted(truth)!r}"
    assert truth["s119g"][1] == "no sealed s119g-harvest record"
    assert list(truth) == ["s119f", "s119g"], "deterministic sid order"


def test_s119w2_card_body_bytes_are_deterministic() -> None:
    """The body is exactly marker/verdict/basis lines; same truth, same bytes."""
    board = _s119w2_board_module()
    expected = _s119w2_expected_body("s119f", "WIN", "s119f-harvest@ab12cd34")
    assert board.mirror_card_body("s119f", "WIN", "s119f-harvest@ab12cd34") == expected


def test_s119w2_card_identity_is_the_season_marker_line() -> None:
    """A card's first `season: <sid>` line claims it; no marker, no claim."""
    board = _s119w2_board_module()
    claimed = "intro text first\nseason: s119f\nverdict: WIN\n"
    assert board._card_sid(claimed) == "s119f"
    assert board._card_sid("operator context, no marker") is None
    assert board._card_sid("season:   \n") is None, "an empty marker claims nothing"


def test_s119w2_plan_creates_updates_and_skips_matches() -> None:
    """create for no card, update for drift, NOTHING for a match; foreign
    cards never plan (no marker; or a marker naming a season with no
    local verdict row -- the s66 lesson, mirrored, never censored)."""
    board = _s119w2_board_module()
    truth = {
        "s119f": ("WIN", "s119f-harvest@ab12cd34"),
        "s98": ("LOSS", "no sealed s98-harvest record"),
        "s120": ("NEUTRAL", "s120-harvest@11223344"),
    }
    cards = [
        _s119w2_card(901, "operator context, no marker"),
        _s119w2_card(904, "season: s999\nverdict: WIN\n"),
        _s119w2_card(902, _s119w2_expected_body("s98", "WIN", "old drift")),
        _s119w2_card(903, _s119w2_expected_body("s120", "NEUTRAL", "s120-harvest@11223344")),
    ]
    plan = board.mirror_plan(truth, cards)
    assert [(row["action"], row["sid"]) for row in plan] == [
        ("create", "s119f"),
        ("update", "s98"),
    ], f"plan rows: {[(r['action'], r['sid']) for r in plan]!r}"
    assert plan[0]["body"] == _s119w2_expected_body(
        "s119f", "WIN", "s119f-harvest@ab12cd34"
    )
    assert plan[1]["number"] == 902, "the update names the live issue number"
    assert plan[1]["body"] == _s119w2_expected_body(
        "s98", "LOSS", "no sealed s98-harvest record"
    )


def test_s119w2_duplicate_markers_first_wins() -> None:
    """Two cards claiming the season: the FIRST in board order claims it;
    the plan updates that one and never touches the duplicate."""
    board = _s119w2_board_module()
    truth = {"s119f": ("WIN", "s119f-harvest@ab12cd34")}
    cards = [
        _s119w2_card(910, _s119w2_expected_body("s119f", "LOSS", "stale")),
        _s119w2_card(911, _s119w2_expected_body("s119f", "WIN", "s119f-harvest@ab12cd34")),
    ]
    plan = board.mirror_plan(truth, cards)
    assert [(r["action"], r["sid"], r["number"]) for r in plan] == [
        ("update", "s119f", 910)
    ], f"plan rows: {[(r['action'], r['number']) for r in plan]!r}"


def test_s119w2_dry_run_renders_and_writes_nothing(tmp_path: Path) -> None:
    """--dry-run renders the plan bytes and mutates nothing through the seam."""
    board = _s119w2_board_module()
    root = _s119w2_root(tmp_path)
    _s119w2_sealed_harvest(root, "s119f")
    _s119w2_verdicts(root, "s119f", '{"season": "s119f", "verdict": "WIN"}')
    _s119w2_verdicts(root, "s98", '{"season": "s98", "verdict": "NEUTRAL"}')
    cards = [
        _s119w2_card(
            912, _s119w2_expected_body("s98", "WIN", "no sealed s98-harvest record")
        ),
    ]
    before = _s119w2_tree_bytes(root)

    def boom(*args: object) -> str:
        raise AssertionError("the dry run must not mutate")

    rendered = board.mirror_sync(root, dry_run=True, trail_fn=lambda: cards, run=boom)
    expected = "\n".join(
        [
            "board mirror (dry-run): nothing written",
            "create s119f",
            "update s98 (#912)",
        ]
    )
    assert rendered == expected, f"render mismatch:\n{rendered!r}\n!=\n{expected!r}"
    assert _s119w2_tree_bytes(root) == before, "the dry run wrote files"


def test_s119w2_dry_run_no_drift_renders_the_honest_nothing(tmp_path: Path) -> None:
    """Everything matching: the no-drift line, zero mutations."""
    board = _s119w2_board_module()
    root = _s119w2_root(tmp_path)
    _s119w2_sealed_harvest(root, "s119f")
    _s119w2_verdicts(root, "s119f", '{"season": "s119f", "verdict": "WIN"}')
    basis = board.ledger_truth(root)["s119f"][1]
    matching = _s119w2_card(930, _s119w2_expected_body("s119f", "WIN", basis))

    def boom(*args: object) -> str:
        raise AssertionError("no drift means no mutation")

    rendered = board.mirror_sync(
        root, dry_run=True, trail_fn=lambda: [matching], run=boom
    )
    assert rendered == (
        "board mirror (dry-run): nothing written\n"
        "no drift: the board matches the ledger"
    ), f"render mismatch: {rendered!r}"


def test_s119w2_live_sync_applies_through_one_seam(tmp_path: Path) -> None:
    """Live: create -> item-add (the url off the create stdout) -> edit,
    exact argv built inline, in plan order, through the ONE run seam."""
    board = _s119w2_board_module()
    root = _s119w2_root(tmp_path)
    _s119w2_sealed_harvest(root, "s119f")
    _s119w2_verdicts(root, "s119f", '{"season": "s119f", "verdict": "WIN"}')
    _s119w2_verdicts(root, "s98", '{"season": "s98", "verdict": "LOSS"}')
    basis_f = board.ledger_truth(root)["s119f"][1]
    bodies = {
        "s119f": _s119w2_expected_body("s119f", "WIN", basis_f),
        "s98": _s119w2_expected_body("s98", "LOSS", "no sealed s98-harvest record"),
    }
    cards = [
        _s119w2_card(912, _s119w2_expected_body("s98", "WIN", "old drift")),
        _s119w2_card(930, "operator context, no marker"),
    ]
    seen: list[list[str]] = []

    def run(argv: list[str]) -> str:
        seen.append(list(argv))
        if argv[2:3] == ["create"]:
            return S119W2_URL_NEW + "\n"
        return ""

    receipt = board.mirror_sync(root, dry_run=False, trail_fn=lambda: cards, run=run)
    expected_calls = [
        [
            "gh", "issue", "create", "-R", "khursanirevo/rumpun",
            "--title", "s119f", "--body", bodies["s119f"],
        ],
        [
            "gh", "project", "item-add", "1",
            "--owner", "khursanirevo", "--url", S119W2_URL_NEW,
        ],
        [
            "gh", "issue", "edit", "912",
            "-R", "khursanirevo/rumpun", "--body", bodies["s98"],
        ],
    ]
    assert seen == expected_calls, f"seam saw: {seen!r}"
    assert receipt.startswith("board mirror: applied"), f"receipt: {receipt!r}"
    assert "create s119f" in receipt and "update s98 (#912)" in receipt

    seen2: list[list[str]] = []

    def failing(argv: list[str]) -> str:
        seen2.append(list(argv))
        if argv[2:3] == ["edit"]:
            raise board.BoardError("gh exited 1: edit rejected")
        return S119W2_URL_NEW + "\n"

    with pytest.raises(board.BoardError, match="edit rejected"):
        board.mirror_sync(root, dry_run=False, trail_fn=lambda: cards, run=failing)
    assert [argv[2] for argv in seen2] == ["create", "item-add", "edit"], seen2


def test_s119w2_second_run_changes_nothing(tmp_path: Path) -> None:
    """Idempotence end to end (pure): apply the plan to the fixture cards,
    re-plan -> empty -- the second run invents and mutates nothing."""
    board = _s119w2_board_module()
    root = _s119w2_root(tmp_path)
    _s119w2_sealed_harvest(root, "s119f")
    _s119w2_verdicts(root, "s119f", '{"season": "s119f", "verdict": "WIN"}')
    truth = board.ledger_truth(root)
    cards: list[dict[str, Any]] = []
    next_number = 950
    plan1 = board.mirror_plan(truth, cards)
    assert [row["action"] for row in plan1] == ["create"], f"plan1: {plan1!r}"
    for row in plan1:
        cards.append(_s119w2_card(next_number, row["body"]))
        next_number += 1
    plan2 = board.mirror_plan(truth, cards)
    assert plan2 == [], f"the second run must plan nothing: {plan2!r}"


def test_s119w2_cli_mirror_flag_parses_and_dispatches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI surface: `board --mirror --dry-run` prints the render, exits
    0, mutates nothing; the positional snapshot form keeps parsing."""
    board = _s119w2_board_module()
    root = _s119w2_root(tmp_path)
    _s119w2_sealed_harvest(root, "s119f")
    _s119w2_verdicts(root, "s119f", '{"season": "s119f", "verdict": "WIN"}')
    from rumpun import cli as cli_module
    basis = board.ledger_truth(root)["s119f"][1]
    matching = _s119w2_card(930, _s119w2_expected_body("s119f", "WIN", basis))

    def boom(*args: object) -> str:
        raise AssertionError("the CLI dry run must not mutate")

    monkeypatch.setattr(board, "issue_trail", lambda *a, **k: [matching])
    monkeypatch.setattr(board, "_bounded_run_out", boom)
    monkeypatch.chdir(root.parent)
    rc = cli_module.main(["board", "--mirror", "--dry-run"])
    assert rc == 0, "the CLI mirror dry run did not exit 0"
    assert capsys.readouterr().out == (
        "board mirror (dry-run): nothing written\n"
        "no drift: the board matches the ledger\n"
    ), "the CLI did not print the exact render"
    parser = cli_module.build_parser()
    parsed = parser.parse_args(["board", "--mirror", "--dry-run"])
    assert parsed.mirror is True
    assert parsed.dry_run is True
    assert parsed.id is None
    parsed_pos = parser.parse_args(["board", "s1"])
    assert parsed_pos.mirror is False, "the snapshot form parses on unchanged"
    parsed_sync = parser.parse_args(["board", "--sync", "s74f"])
    assert parsed_sync.mirror is False, "the --sync form parses on unchanged"


def test_s119w2_corrupt_verdict_file_raises(tmp_path: Path) -> None:
    """A corrupt verdict file is a real read error: it propagates, never
    silently shrinks the truth (the honest-error discipline)."""
    board = _s119w2_board_module()
    root = _s119w2_root(tmp_path)
    _s119w2_verdicts(root, "s119f", "{not json")

    def boom(*args: object) -> str:
        raise AssertionError("no gh call may run on a read error")

    with pytest.raises(ValueError):
        board.mirror_sync(root, dry_run=True, trail_fn=lambda: [], run=boom)
