"""s78 w1 pins — the board map: emission and the sync wiring.

Spec source: .rumpun/runs/s78/w1/prompt.md. Offline: these pins make no
gh call -- the --map existence check runs through the monkeypatched
_bounded_run seam, sync through pickup_fn/run booms. The one live read
lives outside this file: `rumpun board --map s75 <issue #1 url>` then
`rumpun board --sync s75 --dry-run` in the repo, recorded verbatim in
.rumpun/runs/s78/w1/notes.md.

Contract these pins hold -- src/rumpun/board.py + the cli wiring:

1. emit_lane_map(root, sid, issue_url): merges {lane title: issue url}
   for each of the season's lanes into .rumpun/board-map.json; entries
   for other lanes survive (merge, not clobber); the file lands whole
   (no .tmp residue). Refuses with BoardError, writing nothing, on an
   empty url and on a lane-less season.
2. issue_exists_argv(url) is ["gh", "issue", "view", url] -- the one
   rc-gated existence call the CLI runs before any write.
3. The CLI surface: `rumpun board --map SID URL` checks first (the
   check precedes the write; a dead url exits 1 and writes nothing),
   then writes the map and prints a receipt naming the season's lanes.
4. Sync reads the emitted map before any fallback: after emit_lane_map,
   sync_season resolves the url with pickup/run booms -- nothing live
   is consulted. The s76 recorded gap is closed end to end.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

S78W1_URL_A = "https://github.com/khursanirevo/rumpun/issues/781"
S78W1_URL_OLD = "https://github.com/khursanirevo/rumpun/issues/780"
S78W1_URL_PRE = "https://github.com/khursanirevo/rumpun/issues/779"
S78W1_URL_MISSING = "https://github.com/khursanirevo/rumpun/issues/999"

S78W1_LANE_A = "s78-lane-map-a"
S78W1_LANE_B = "s78-lane-map-b"

S78W1_SEASON_YAML = """\
id: s78f
parent: s78
goal: fixture season for the s78 w1 board-map pins
metric: modules_integrated
writers:
  - name: w1
    lane: s78-lane-map-a
  - name: w2
    lane: s78-lane-map-b
"""

S78W1_HARVEST_BODY = (
    "season s78f: completed\n"
    "duration: 60s\n"
    "\n"
    "| agent | route | state | exit_code | seconds |\n"
    "|---|---|---|---|---|\n"
    "| w1 | fable | exited | 0 | 60.0 |\n"
    "\n"
    "verdict: WIN\n"
    "implies: the board-map pins hold offline\n"
)


def _s78w1_board_module():
    """Import rumpun.board; fail naming the spec reason when unlanded."""
    try:
        from rumpun import board as board_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/board.py missing/unimportable: {exc}")
    return board_module


def _s78w1_campaign(tmp_path: Path) -> Path:
    """A fresh .rumpun root: rumpun.yaml + the fixture season s78f.

    The season yaml declares two writers whose lanes are the map keys
    (s78-lane-map-a, s78-lane-map-b); the ledger starts empty.
    """
    campaign = tmp_path / "s78w1proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        "autonomy:\n  stage: manual\n", encoding="utf-8"
    )
    (root / "seasons" / "s78f.yaml").write_text(S78W1_SEASON_YAML, encoding="utf-8")
    return root


def _s78w1_sealed_harvest(root: Path) -> Path:
    """Append the s78f-harvest record through akar itself, so the seal is real."""
    from rumpun import akar

    return akar.append_record(
        root, "s78f-harvest", "season s78f harvest", S78W1_HARVEST_BODY
    )


def _s78w1_map(root: Path, payload: dict[str, str] | None) -> None:
    """Seed (or remove, payload None) the fixture lane map."""
    path = root / "board-map.json"
    if payload is None:
        path.unlink(missing_ok=True)
        return
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _s78w1_tree_bytes(root: Path) -> dict[str, bytes]:
    """Every file under root as {relative path: bytes}, for write-nothing pins."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_s78w1_emit_lane_map_writes_the_seasons_lanes(tmp_path: Path) -> None:
    """One emission maps every lane of the season to the one issue url.

    The returned merged dict equals the file's parsed content, and no
    .board-map.json.tmp residue survives the atomic replace.
    """
    board = _s78w1_board_module()
    root = _s78w1_campaign(tmp_path)
    merged = board.emit_lane_map(root, "s78f", S78W1_URL_A)
    assert merged == {S78W1_LANE_A: S78W1_URL_A, S78W1_LANE_B: S78W1_URL_A}
    data = json.loads((root / "board-map.json").read_text(encoding="utf-8"))
    assert data == merged, "the file must hold exactly the returned merge"
    assert not (root / ".board-map.json.tmp").exists(), "tmp residue left behind"


def test_s78w1_emit_lane_map_merges_existing_entries_survive(tmp_path: Path) -> None:
    """Merge, not clobber: another lane's entry survives; a re-mapped lane refreshes."""
    board = _s78w1_board_module()
    root = _s78w1_campaign(tmp_path)
    _s78w1_map(root, {"other-seasons-lane": S78W1_URL_PRE, S78W1_LANE_A: S78W1_URL_OLD})
    board.emit_lane_map(root, "s78f", S78W1_URL_A)
    data = json.loads((root / "board-map.json").read_text(encoding="utf-8"))
    assert data["other-seasons-lane"] == S78W1_URL_PRE, "a foreign entry was clobbered"
    assert data[S78W1_LANE_A] == S78W1_URL_A, "the re-mapped lane must refresh"
    assert data[S78W1_LANE_B] == S78W1_URL_A, "the second lane must be added"


def test_s78w1_emit_lane_map_refuses_empty_url_and_laneless_season(
    tmp_path: Path,
) -> None:
    """BoardError on an empty url and on a lane-less season; nothing written."""
    board = _s78w1_board_module()
    root = _s78w1_campaign(tmp_path)
    before = _s78w1_tree_bytes(root)
    with pytest.raises(board.BoardError, match="empty issue url"):
        board.emit_lane_map(root, "s78f", "")
    assert _s78w1_tree_bytes(root) == before, "the empty-url refusal wrote files"
    (root / "seasons" / "s78g.yaml").write_text(
        "id: s78g\nwriters:\n  - name: w1\n", encoding="utf-8"
    )
    before_g = _s78w1_tree_bytes(root)
    with pytest.raises(board.BoardError, match="s78g has no lanes to map"):
        board.emit_lane_map(root, "s78g", S78W1_URL_A)
    with pytest.raises(board.BoardError, match="no lanes to map"):
        board.emit_lane_map(root, "s99", S78W1_URL_A)
    assert _s78w1_tree_bytes(root) == before_g, "a refusal wrote files"


def test_s78w1_issue_exists_argv_matches_gh() -> None:
    """The existence check is one gh call, argv-exact, no -R (URL carries the repo)."""
    board = _s78w1_board_module()
    assert board.issue_exists_argv(S78W1_URL_A) == ["gh", "issue", "view", S78W1_URL_A]


def test_s78w1_sync_reads_the_emitted_map_before_any_fallback(tmp_path: Path) -> None:
    """End to end offline: emit, then sync --dry-run resolves through the map.

    pickup_fn and run booms prove nothing live is consulted: the emitted
    map alone resolves the url. The render is constructed inline (not via
    render_sync), so the pin is independent of the implementation's renderer.
    """
    board = _s78w1_board_module()
    root = _s78w1_campaign(tmp_path)
    record_path = _s78w1_sealed_harvest(root)
    board.emit_lane_map(root, "s78f", S78W1_URL_A)
    before = _s78w1_tree_bytes(root)

    def boom(*args: object) -> None:
        raise AssertionError("the emitted map must make sync skip pickup/run")

    rendered = board.sync_season(
        root, "s78f", dry_run=True, pickup_fn=boom, run=boom  # type: ignore[arg-type]
    )
    expected = "\n".join(
        [
            "board sync s78f (dry-run): nothing written",
            f"comment {S78W1_URL_A} with {record_path} (verbatim, sealed)",
            f"close {S78W1_URL_A}",
        ]
    )
    assert rendered == expected, f"render mismatch:\n{rendered!r}\n!=\n{expected!r}"
    assert _s78w1_tree_bytes(root) == before, "the dry run wrote files"


def test_s78w1_cli_board_map_checks_then_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI: one existence check (rc-gated seam) BEFORE the write, then the map.

    The fake seam records its argv and asserts the map is absent at check
    time -- the check must precede the write. The receipt is byte-checked.
    """
    board = _s78w1_board_module()
    root = _s78w1_campaign(tmp_path)
    from rumpun import cli as cli_module

    seen: list[list[str]] = []

    def fake_run(argv: list[str]) -> None:
        seen.append(argv)
        assert not (root / "board-map.json").exists(), "the check must precede the write"

    monkeypatch.setattr(board, "_bounded_run", fake_run)
    monkeypatch.chdir(root.parent)
    rc = cli_module.main(["board", "--map", "s78f", S78W1_URL_A])
    assert rc == 0, "the CLI --map did not exit 0"
    assert seen == [["gh", "issue", "view", S78W1_URL_A]], f"seam saw: {seen!r}"
    data = json.loads((root / "board-map.json").read_text(encoding="utf-8"))
    assert data == {S78W1_LANE_A: S78W1_URL_A, S78W1_LANE_B: S78W1_URL_A}
    expected = "\n".join(
        [
            f"board map s78f -> {S78W1_URL_A}",
            f"  {S78W1_LANE_A} -> {S78W1_URL_A}",
            f"  {S78W1_LANE_B} -> {S78W1_URL_A}",
            f"map: {root / board.BOARD_MAP_FILE}",
        ]
    ) + "\n"
    assert capsys.readouterr().out == expected, "the receipt is not the exact bytes"


def test_s78w1_cli_board_map_dead_issue_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dead url: the rc-gated check refuses; exit 1, no map file, nothing written."""
    board = _s78w1_board_module()
    root = _s78w1_campaign(tmp_path)
    from rumpun import cli as cli_module

    def dead(argv: list[str]) -> None:
        raise board.BoardError("gh exited 1: Could not resolve to an Issue")

    monkeypatch.setattr(board, "_bounded_run", dead)
    monkeypatch.chdir(root.parent)
    before = _s78w1_tree_bytes(root)
    rc = cli_module.main(["board", "--map", "s78f", S78W1_URL_MISSING])
    assert rc == 1, "the CLI must exit 1 on the refused check"
    assert _s78w1_tree_bytes(root) == before, "a dead url wrote files"


def test_s78w1_board_verb_surface_parses_map() -> None:
    """--map takes SID and ISSUE-URL; the older surfaces parse unchanged."""
    from rumpun import cli as cli_module

    parser = cli_module.build_parser()
    parsed = parser.parse_args(["board", "--map", "s75", S78W1_URL_A])
    assert parsed.map == ["s75", S78W1_URL_A]
    assert parsed.sync is None
    assert parsed.id is None
    assert parsed.dry_run is False
    parsed_pos = parser.parse_args(["board", "s1"])
    assert parsed_pos.id == "s1"
    assert parsed_pos.map is None
    parsed_sync = parser.parse_args(["board", "--sync", "s78f", "--dry-run"])
    assert parsed_sync.sync == "s78f"
    assert parsed_sync.dry_run is True
    assert parsed_sync.map is None
