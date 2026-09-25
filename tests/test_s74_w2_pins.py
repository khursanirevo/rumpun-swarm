"""s74 w2 pins — the board lifecycle: a sealed harvest closes its issue.

Spec source: .rumpun/runs/s74/w2/prompt.md (the s74 w2 brief); the s73
panel pins are the seam-and-fixtures precedent, the s69 board pins are
the argv precedent. Offline: these pins make no gh call -- the live
seams are injected (pickup_fn, run) or monkeypatched (board.pickup).
The one live read lives outside this file: `rumpun board --sync s73
--dry-run` in the repo, recorded in .rumpun/runs/s74/w2/notes.md.

Contract these pins hold -- src/rumpun/board.py + the cli wiring:

1. Builders, argv-exact: harvest_comment_argv(issue_url, record_path)
   is ["gh", "issue", "comment", issue_url, "--body-file",
   str(record_path)] -- the record file IS the verbatim body, seal
   included, and the URL carries the repo so no -R flag;
   close_issue_argv(issue_url) is ["gh", "issue", "close", issue_url].
2. issue_for_season(root, sid): the committed lane map
   (.rumpun/board-map.json, flat {lane title: issue url}) wins, each
   lane of the season in writers order; else the first pickup row
   (board order) whose issue title is a lane title of the season
   (issues carry the season's lane title). None when unmapped: a
   missing season yaml, no lanes, no map hit, no title match. A corrupt
   map is a BoardError, never a silent fallback.
3. sync_season(root, sid, dry_run): refuses a season with no harvest
   record (akar.AkarError), a broken sha256 seal (BoardError), an
   unmapped season (BoardError), a failed live pickup (BoardError).
   --dry-run returns the render bytes and writes nothing, calls
   nothing. Live: comment BEFORE close through the injected seam with
   the exact builder argv; a comment failure never runs the close.
4. The CLI surface: `rumpun board --sync SID --dry-run` prints the
   render (byte-checked via capsys) and exits 0 writing nothing; the
   positional form parses on (the P36 snapshot dispatch survives).
"""


from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

S74W2_URL_A = "https://github.com/khursanirevo/rumpun/issues/741"
S74W2_URL_B = "https://github.com/khursanirevo/rumpun/issues/742"
S74W2_URL_DECOY = "https://github.com/khursanirevo/rumpun/issues/743"
S74W2_URL_UNRELATED = "https://github.com/khursanirevo/rumpun/issues/744"

S74W2_LANE_A = "lane-map-fixture-a"
S74W2_LANE_B = "lane-map-fixture-b"

S74W2_SEASON_YAML = """\
id: s74f
parent: s74
goal: fixture season for the s74 w2 lifecycle pins
metric: modules_integrated
writers:
  - name: w1
    lane: lane-map-fixture-a
  - name: w2
    lane: lane-map-fixture-b
"""

S74W2_HARVEST_BODY = (
    "season s74f: completed\n"
    "duration: 60s\n"
    "\n"
    "| agent | route | state | exit_code | seconds |\n"
    "|---|---|---|---|---|\n"
    "| w1 | fable | exited | 0 | 60.0 |\n"
    "\n"
    "verdict: WIN\n"
    "implies: the lifecycle pins hold offline\n"
)


def _s74w2_repo_root() -> Path:
    """Repo root from this file's location, workspace and merged alike.

    The s70/s71 walk-up rule: parents[] must hold pyproject.toml,
    src/rumpun/report.py and DESIGN.md together, so archived src/ copies
    in scratch trees never match.
    """
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s74w2_board_module():
    """Import rumpun.board; fail naming the spec reason when unlanded."""
    try:
        from rumpun import board as board_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/board.py missing/unimportable: {exc}")
    return board_module


def _s74w2_campaign(tmp_path: Path) -> Path:
    """A fresh .rumpun root: rumpun.yaml + the fixture season s74f.

    The season yaml declares two writers whose lanes are the map keys
    (lane-map-fixture-a, lane-map-fixture-b); the ledger starts empty.
    """
    campaign = tmp_path / "s74w2proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        "autonomy:\n  stage: manual\n", encoding="utf-8"
    )
    (root / "seasons" / "s74f.yaml").write_text(S74W2_SEASON_YAML, encoding="utf-8")
    return root


def _s74w2_sealed_harvest(root: Path) -> Path:
    """Append the s74f-harvest record through akar itself, so the seal is real."""
    from rumpun import akar

    return akar.append_record(
        root, "s74f-harvest", "season s74f harvest", S74W2_HARVEST_BODY
    )


def _s74w2_map(root: Path, payload: dict[str, str] | None) -> None:
    """Write (or remove, payload None) the fixture lane map."""
    import json

    path = root / "board-map.json"
    if payload is None:
        path.unlink(missing_ok=True)
        return
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _s74w2_rows(*rows: dict[str, str]) -> list[dict[str, str]]:
    return list(rows)


def _s74w2_tree_bytes(root: Path) -> dict[str, bytes]:
    """Every file under root as {relative path: bytes}, for write-nothing pins."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _s74w2_row(state: str, title: str, url: str) -> dict[str, str]:
    return {"state": state, "title": title, "url": url}


def test_s74w2_lifecycle_argv_matches_gh_commands(tmp_path: Path) -> None:
    """Pin argv equality for both lifecycle commands; no gh call."""
    board = _s74w2_board_module()
    record = tmp_path / "2026-09-17_s74f-harvest.md"
    record.write_text("# akar record: s74f-harvest\n", encoding="utf-8")
    url = S74W2_URL_A
    assert board.harvest_comment_argv(url, record) == [
        "gh",
        "issue",
        "comment",
        url,
        "--body-file",
        str(record),
    ]
    assert board.close_issue_argv(url) == ["gh", "issue", "close", url]


def test_s74w2_lane_map_hit_and_precedence(tmp_path: Path) -> None:
    """A map hit wins for the season's lanes, in writers order.

    The pickup fallback is never consulted on a map hit: the injected
    rows carry a DIFFERENT url for lane A, so returning the map url
    proves the map won.
    """
    board = _s74w2_board_module()
    root = _s74w2_campaign(tmp_path)
    _s74w2_map(root, {S74W2_LANE_A: S74W2_URL_A})

    def rows() -> list[dict[str, str]]:
        return _s74w2_rows(
            _s74w2_row("OPEN", S74W2_LANE_A, S74W2_URL_DECOY),
            _s74w2_row("CLOSED", S74W2_LANE_B, S74W2_URL_B),
        )

    assert board.issue_for_season(root, "s74f", pickup_fn=rows) == S74W2_URL_A


def test_s74w2_map_covers_the_second_lane_before_any_fallback(tmp_path: Path) -> None:
    """All lanes check the map BEFORE the fallback runs: lanes [a, b],
    map holds only b -> b's map url, the pickup rows never consulted."""
    board = _s74w2_board_module()
    root = _s74w2_campaign(tmp_path)
    _s74w2_map(root, {S74W2_LANE_B: S74W2_URL_B})

    def boom() -> list[dict[str, str]]:
        raise AssertionError("the fallback must not run when the map hits")

    assert board.issue_for_season(root, "s74f", pickup_fn=boom) == S74W2_URL_B


def test_s74w2_fallback_title_match_on_pickup_rows(tmp_path: Path) -> None:
    """No map: the first pickup row (board order) titled with a lane wins.

    The rows deliberately carry lane B before lane A while the season's
    writers order is lane A first -- the board order wins among matches,
    the writers order only orders the map lookup.
    """
    board = _s74w2_board_module()
    root = _s74w2_campaign(tmp_path)
    _s74w2_map(root, None)

    def rows() -> list[dict[str, str]]:
        return _s74w2_rows(
            _s74w2_row("OPEN", "unrelated issue", S74W2_URL_UNRELATED),
            _s74w2_row("OPEN", S74W2_LANE_B, S74W2_URL_B),
            _s74w2_row("CLOSED", S74W2_LANE_A, S74W2_URL_A),
        )

    assert board.issue_for_season(root, "s74f", pickup_fn=rows) == S74W2_URL_B


def test_s74w2_unmapped_cases_return_none(tmp_path: Path) -> None:
    """None when: no season yaml, no lanes, no match; corrupt map refuses."""
    board = _s74w2_board_module()
    root = _s74w2_campaign(tmp_path)

    def rows() -> list[dict[str, str]]:
        return _s74w2_rows(_s74w2_row("OPEN", "unrelated issue", S74W2_URL_UNRELATED))

    # Missing season yaml.
    assert board.issue_for_season(root, "s99", pickup_fn=rows) is None
    # Lanes exist, no map, no title match.
    assert board.issue_for_season(root, "s74f", pickup_fn=rows) is None
    # A draft-only season (no lane keys) is unmapped too.
    (root / "seasons" / "s74g.yaml").write_text(
        "id: s74g\nwriters:\n  - name: w1\n", encoding="utf-8"
    )
    assert board.issue_for_season(root, "s74g", pickup_fn=rows) is None
    # A corrupt map is a BoardError, never a silent fallback.
    (root / "board-map.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(board.BoardError, match="not valid JSON"):
        board.issue_for_season(root, "s74f", pickup_fn=rows)


def test_s74w2_dry_run_renders_bytes_and_writes_nothing(tmp_path: Path) -> None:
    """--dry-run returns the exact render and writes nothing, calls nothing.

    The expected bytes are constructed inline here (not via
    render_sync), so the pin is independent of the implementation's
    renderer. pickup and run booms prove nothing live is consulted.
    """
    board = _s74w2_board_module()
    root = _s74w2_campaign(tmp_path)
    record_path = _s74w2_sealed_harvest(root)
    _s74w2_map(root, {S74W2_LANE_A: S74W2_URL_A})
    before = _s74w2_tree_bytes(root)
    from rumpun import akar

    def boom(*args: object) -> None:
        raise AssertionError("the dry run must not call pickup or run")

    rendered = board.sync_season(
        root, "s74f", dry_run=True, pickup_fn=boom, run=boom  # type: ignore[arg-type]
    )
    expected = "\n".join(
        [
            "board sync s74f (dry-run): nothing written",
            f"comment {S74W2_URL_A} with {record_path} (verbatim, sealed)",
            f"close {S74W2_URL_A}",
        ]
    )
    assert rendered == expected, f"render mismatch:\n{rendered!r}\n!=\n{expected!r}"
    assert _s74w2_tree_bytes(root) == before, "the dry run wrote files"
    assert list(akar.declared_ids(root)) == ["s74f-harvest"], "the dry run wrote records"


def test_s74w2_live_sync_comments_then_closes_through_the_seam(tmp_path: Path) -> None:
    """Live: comment BEFORE close, exact builder argv, receipt rendered.

    The expected argv are constructed literally (builder-independent).
    A comment failure strands the issue open: the close never runs.
    """
    board = _s74w2_board_module()
    root = _s74w2_campaign(tmp_path)
    record_path = _s74w2_sealed_harvest(root)
    _s74w2_map(root, {S74W2_LANE_A: S74W2_URL_A})
    comment_argv = [
        "gh",
        "issue",
        "comment",
        S74W2_URL_A,
        "--body-file",
        str(record_path),
    ]
    close_argv = ["gh", "issue", "close", S74W2_URL_A]

    seen: list[list[str]] = []
    receipt = board.sync_season(root, "s74f", dry_run=False, run=seen.append)
    assert seen == [comment_argv, close_argv], f"seam saw: {seen!r}"
    assert receipt.startswith("board sync s74f: commented and closed"), (
        f"no live receipt: {receipt!r}"
    )
    assert f"comment {S74W2_URL_A} with {record_path} (verbatim, sealed)" in receipt
    assert f"close {S74W2_URL_A}" in receipt

    seen_failure: list[list[str]] = []
    seen_failure.append("sentinel")  # keep mypy quiet about the unused hint

    def failing(argv: list[str]) -> None:
        seen_failure.append(argv)
        raise board.BoardError("gh exited 4: comment rejected")

    with pytest.raises(board.BoardError, match="comment rejected"):
        board.sync_season(root, "s74f", dry_run=False, run=failing)
    assert seen_failure[1:] == [comment_argv], f"the close must not run: {seen_failure!r}"


def test_s74w2_sync_refuses_unharvested_unsealed_and_unmapped(tmp_path: Path) -> None:
    """Three honest refusals: no record (AkarError), broken seal, unmapped."""
    board = _s74w2_board_module()
    from rumpun import akar

    # No harvest record: akar's own refusal names the id.
    root = _s74w2_campaign(tmp_path)
    _s74w2_map(root, {S74W2_LANE_A: S74W2_URL_A})
    with pytest.raises(akar.AkarError, match="s74f-harvest"):
        board.sync_season(root, "s74f", dry_run=True, pickup_fn=lambda: [])

    # Broken seal: a body byte edited after sealing refuses.
    root_tampered = _s74w2_campaign(tmp_path / "tampered")
    record_path = _s74w2_sealed_harvest(root_tampered)
    _s74w2_map(root_tampered, {S74W2_LANE_A: S74W2_URL_A})
    lines = record_path.read_text(encoding="utf-8").splitlines()
    tampered = "\n".join(
        ["verdict: LOSS" if line == "verdict: WIN" else line for line in lines]
    )
    record_path.write_text(tampered + "\n", encoding="utf-8")
    with pytest.raises(board.BoardError, match="seal"):
        board.sync_season(root_tampered, "s74f", dry_run=True, pickup_fn=lambda: [])

    # Unmapped: sealed harvest, no map, no title match.
    root_unmapped = _s74w2_campaign(tmp_path / "unmapped")
    _s74w2_sealed_harvest(root_unmapped)
    _s74w2_map(root_unmapped, None)
    with pytest.raises(board.BoardError, match="unmapped"):
        board.sync_season(
            root_unmapped, "s74f", dry_run=True, pickup_fn=lambda: []
        )


def test_s74w2_cli_board_sync_dry_run_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI surface: main(['board', '--sync', 's74f', '--dry-run']) prints
    the render and exits 0 writing nothing; board.pickup stays untouched."""
    board = _s74w2_board_module()
    root = _s74w2_campaign(tmp_path)
    _s74w2_sealed_harvest(root)
    _s74w2_map(root, {S74W2_LANE_A: S74W2_URL_A})
    record_path = root / "ledger" / f"{date.today().isoformat()}_s74f-harvest.md"
    from rumpun import cli as cli_module

    def boom(*args: object) -> list[dict[str, str]]:
        raise AssertionError("the CLI dry run must not call pickup")

    monkeypatch.setattr(board, "pickup", boom)
    monkeypatch.chdir(root.parent)
    before = _s74w2_tree_bytes(root)
    rc = cli_module.main(["board", "--sync", "s74f", "--dry-run"])
    assert rc == 0, "the CLI dry run did not exit 0"
    expected = (
        "board sync s74f (dry-run): nothing written\n"
        f"comment {S74W2_URL_A} with {record_path} (verbatim, sealed)\n"
        f"close {S74W2_URL_A}\n"
    )
    assert capsys.readouterr().out == expected, "the CLI did not print the exact render"
    assert _s74w2_tree_bytes(root) == before, "the CLI dry run wrote files"


def test_s74w2_board_verb_surface_keeps_positional_id() -> None:
    """The positional form parses on: id, no sync, dry_run False, snapshot fn."""
    from rumpun import cli as cli_module

    parser = cli_module.build_parser()
    parsed = parser.parse_args(["board", "s1"])
    assert parsed.id == "s1"
    assert parsed.sync is None
    assert parsed.dry_run is False
    parsed_sync = parser.parse_args(["board", "--sync", "s74f", "--dry-run"])
    assert parsed_sync.id is None
    assert parsed_sync.sync == "s74f"
    assert parsed_sync.dry_run is True
