"""s78 w2 pins — the board map: emission, lookup order, verb gate, dry run.

Spec source: .rumpun/runs/s78/w2/prompt.md (the s78 w2 brief). The w1
lane lands emit_lane_map + the `board --map <sid> <issue-url>` verb
mid-flight; these pins are the spec-first contract held offline: no gh
call, no network, the live evidence stays in w1's notes.md. Pins over
already-landed surface (the lookup order, the map-fed dry run) run
green today; pins over the unlanded emission + verb fail until w1's
merge turns them green (the split is recorded in notes.md).

Contract these pins hold -- src/rumpun/board.py + the cli wiring:

1. emit_lane_map(root, sid, issue_url) -> merged dict: creates
   .rumpun/board-map.json when absent, valid JSON, flat {lane title:
   issue url} for the season's lanes; merges -- entries for other
   lanes survive; a re-run is byte-identical; no lanes (or an empty
   url) is a loud BoardError writing nothing -- a map entry must name
   a real issue and a real lane, and a refusal never clobbers.
2. issue_for_season order: a map entry wins over a lane-title pickup
   match (the fallback is never consulted on a map hit); a map that
   misses the lanes falls through to the pickup title match (board
   order); neither -> None, and sync_season then BoardErrors (the s76
   gap behavior). The corrupt-map BoardError stays s74's pin.
3. The --map verb, offline: exactly one gh call naming the issue url,
   and the map write happens only after that check passes (rc 0 -> the
   season's lanes mapped; nonzero -> the verb exits nonzero and the
   map file is untouched: absent stays absent, entries survive).
4. The s75 dry-run shape, map-fed: with the map seeded with issue #1
   and a sealed harvest record, the dry-run render names issue #1 and
   the sealed record, writes nothing, calls nothing live -- at the
   function and through `rumpun board --sync <sid> --dry-run` (rc 0,
   exact stdout).
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from rumpun import akar, board

logger = logging.getLogger(__name__)

S78W2_URL_ISSUE1 = "https://github.com/khursanirevo/rumpun/issues/1"
S78W2_URL_MAP = "https://github.com/khursanirevo/rumpun/issues/811"
S78W2_URL_B = "https://github.com/khursanirevo/rumpun/issues/812"
S78W2_URL_DECOY = "https://github.com/khursanirevo/rumpun/issues/813"
S78W2_URL_UNRELATED = "https://github.com/khursanirevo/rumpun/issues/814"
S78W2_URL_SURVIVOR = "https://github.com/khursanirevo/rumpun/issues/815"

S78W2_LANE_A = "lane-s78w2-a"
S78W2_LANE_B = "lane-s78w2-b"
S78W2_LANE_OTHER = "lane-s78w2-other"

S78W2_SEASON_YAML = """\
id: s78f
parent: s78
goal: fixture season for the s78 w2 board-map pins
metric: modules_integrated
writers:
  - name: w1
    lane: lane-s78w2-a
  - name: w2
    lane: lane-s78w2-b
"""

S78W2_LANELESS_YAML = """\
id: s78g
parent: s78
goal: laneless fixture (writers carry no lane keys)
metric: modules_integrated
writers:
  - name: w1
"""

S78W2_HARVEST_BODY = (
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


def _s78w2_campaign(tmp_path: Path, name: str = "s78w2camp") -> Path:
    """A fresh .rumpun root: rumpun.yaml, the s78f season, empty ledger."""
    campaign = tmp_path / name
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        "autonomy:\n  stage: manual\n", encoding="utf-8"
    )
    (root / "seasons" / "s78f.yaml").write_text(S78W2_SEASON_YAML, encoding="utf-8")
    return root


def _s78w2_sealed(root: Path) -> Path:
    """Append the s78f-harvest record through akar itself, so the seal is real."""
    return akar.append_record(
        root, "s78f-harvest", "season s78f harvest", S78W2_HARVEST_BODY
    )


def _s78w2_seed_map(root: Path, payload: dict[str, str]) -> None:
    """Hand-build the map (no harvest/map verb in fixtures)."""
    (root / board.BOARD_MAP_FILE).write_text(
        json.dumps(payload) + "\n", encoding="utf-8"
    )


def _s78w2_tree_bytes(root: Path) -> dict[str, bytes]:
    """Every file under root as {relative path: bytes}, for write-nothing pins."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _s78w2_fake_check(
    monkeypatch: pytest.MonkeyPatch, rc: int
) -> list[list[str]]:
    """Patch subprocess.run to a recording fake that answers the given rc.

    The verb's issue-existence check is a gh call; whatever seam w1's
    verb uses (direct or _bounded_run), it crosses subprocess.run, so
    this is the seam-agnostic offline gate.
    """
    seen: list[list[str]] = []

    def fake_run(argv: list[str], **kwargs: object) -> SimpleNamespace:
        seen.append(list(argv))
        return SimpleNamespace(returncode=rc, stdout="", stderr="gh: s78w2 fake")

    monkeypatch.setattr(subprocess, "run", fake_run)
    return seen


def test_s78w2_emit_lane_map_creates_the_file_when_absent(tmp_path: Path) -> None:
    """Absent file: emit writes valid JSON mapping the season's lanes."""
    root = _s78w2_campaign(tmp_path)
    board.emit_lane_map(root, "s78f", S78W2_URL_MAP)
    path = root / board.BOARD_MAP_FILE
    assert path.is_file(), "emit did not create board-map.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {
        S78W2_LANE_A: S78W2_URL_MAP,
        S78W2_LANE_B: S78W2_URL_MAP,
    }, f"the map is not the season's lanes -> the issue url: {data!r}"


def test_s78w2_emit_lane_map_merges_existing_entries_survive(tmp_path: Path) -> None:
    """Merge, not clobber: a pre-existing other-lane entry survives emit."""
    root = _s78w2_campaign(tmp_path, name="s78w2merge")
    _s78w2_seed_map(root, {S78W2_LANE_OTHER: S78W2_URL_SURVIVOR})
    board.emit_lane_map(root, "s78f", S78W2_URL_MAP)
    data = json.loads(
        (root / board.BOARD_MAP_FILE).read_text(encoding="utf-8")
    )
    assert data == {
        S78W2_LANE_OTHER: S78W2_URL_SURVIVOR,
        S78W2_LANE_A: S78W2_URL_MAP,
        S78W2_LANE_B: S78W2_URL_MAP,
    }, f"merge lost an entry: {data!r}"


def test_s78w2_emit_lane_map_is_idempotent_on_rerun(tmp_path: Path) -> None:
    """Emitting the same season + url twice is byte-identical."""
    root = _s78w2_campaign(tmp_path, name="s78w2idem")
    board.emit_lane_map(root, "s78f", S78W2_URL_MAP)
    once = (root / board.BOARD_MAP_FILE).read_bytes()
    board.emit_lane_map(root, "s78f", S78W2_URL_MAP)
    twice = (root / board.BOARD_MAP_FILE).read_bytes()
    assert once == twice, "the re-run was not byte-identical"


def test_s78w2_emit_lane_map_refuses_laneless_and_empty_url(tmp_path: Path) -> None:
    """No lanes or an empty url: loud BoardError, and no write either way.

    A map entry must name a real issue and a real lane (the s78 w1
    contract: refuse loud, never a silent {} clobber). The refusal
    writes nothing: absent stays absent, a seeded map stays
    byte-identical.
    """
    root = _s78w2_campaign(tmp_path, name="s78w2nl")
    (root / "seasons" / "s78g.yaml").write_text(
        S78W2_LANELESS_YAML, encoding="utf-8"
    )
    map_path = root / board.BOARD_MAP_FILE

    with pytest.raises(board.BoardError, match="no lanes"):
        board.emit_lane_map(root, "s78g", S78W2_URL_MAP)
    assert not map_path.exists(), "the refused emit created the map"
    with pytest.raises(board.BoardError, match="no lanes"):
        board.emit_lane_map(root, "s78h-missing", S78W2_URL_MAP)
    assert not map_path.exists(), "the refused emit created the map"

    _s78w2_seed_map(root, {S78W2_LANE_OTHER: S78W2_URL_SURVIVOR})
    seeded = map_path.read_bytes()
    with pytest.raises(board.BoardError, match="no lanes"):
        board.emit_lane_map(root, "s78g", S78W2_URL_MAP)
    assert map_path.read_bytes() == seeded, "the refused emit clobbered the map"
    with pytest.raises(board.BoardError, match="empty issue url"):
        board.emit_lane_map(root, "s78f", "")
    assert map_path.read_bytes() == seeded, "the empty-url emit clobbered the map"


def test_s78w2_map_entry_wins_over_a_pickup_match(tmp_path: Path) -> None:
    """Map first: the map url wins and the fallback is never consulted."""
    root = _s78w2_campaign(tmp_path, name="s78w2order")
    _s78w2_seed_map(root, {S78W2_LANE_A: S78W2_URL_MAP})
    calls: list[list[dict[str, str]]] = []

    def rows() -> list[dict[str, str]]:
        calls.append(
            [
                {"state": "OPEN", "title": S78W2_LANE_A, "url": S78W2_URL_DECOY},
                {"state": "CLOSED", "title": S78W2_LANE_B, "url": S78W2_URL_B},
            ]
        )
        return list(calls[-1])

    assert board.issue_for_season(root, "s78f", pickup_fn=rows) == S78W2_URL_MAP
    assert calls == [], "the fallback ran despite the map hit"


def test_s78w2_no_map_entry_falls_through_to_pickup(tmp_path: Path) -> None:
    """Map present but missing the lanes: the pickup title match decides.

    The rows carry lane B before lane A while the season's writers
    order is lane A first -- board order wins among matches.
    """
    root = _s78w2_campaign(tmp_path, name="s78w2fall")
    _s78w2_seed_map(root, {S78W2_LANE_OTHER: S78W2_URL_SURVIVOR})

    def rows() -> list[dict[str, str]]:
        return [
            {"state": "OPEN", "title": "unrelated", "url": S78W2_URL_UNRELATED},
            {"state": "OPEN", "title": S78W2_LANE_B, "url": S78W2_URL_B},
            {"state": "OPEN", "title": S78W2_LANE_A, "url": S78W2_URL_MAP},
        ]

    assert board.issue_for_season(root, "s78f", pickup_fn=rows) == S78W2_URL_B


def test_s78w2_unmapped_is_none_and_sync_refuses(tmp_path: Path) -> None:
    """Neither map nor pickup: None, and sync_season BoardErrors.

    The s76 gap behavior: an unmapped season refuses loudly instead of
    closing nothing. dry_run=True keeps the refusal arm offline even by
    accident.
    """
    root = _s78w2_campaign(tmp_path, name="s78w2none")
    _s78w2_sealed(root)

    def rows() -> list[dict[str, str]]:
        return [
            {"state": "OPEN", "title": "unrelated", "url": S78W2_URL_UNRELATED}
        ]

    assert board.issue_for_season(root, "s78f", pickup_fn=rows) is None
    with pytest.raises(board.BoardError, match="unmapped"):
        board.sync_season(root, "s78f", dry_run=True, pickup_fn=rows)


def test_s78w2_map_verb_gates_the_write_on_the_issue_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """rc 0: one gh call naming the url BEFORE the write; then the map lands.

    The write-after-check ordering is asserted inside the fake check
    itself: when the check runs, the map must not carry the entry yet.
    """
    from rumpun import cli as cli_module

    root = _s78w2_campaign(tmp_path, name="s78w2verb")
    map_path = root / board.BOARD_MAP_FILE

    seen: list[list[str]] = []

    def assert_unwritten(argv: list[str]) -> None:
        assert not map_path.exists(), "the map was written before the check passed"
        assert argv[0] == "gh", f"the check is not a gh call: {argv!r}"
        assert S78W2_URL_MAP in argv, "the check did not name the issue url"

    def fake_run(argv: list[str], **kwargs: object) -> SimpleNamespace:
        assert_unwritten(list(argv))
        seen.append(list(argv))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.chdir(root.parent)
    rc = cli_module.main(["board", "--map", "s78f", S78W2_URL_MAP])
    assert rc == 0, "the passing check did not exit 0"
    assert len(seen) == 1, f"the check must be exactly one call: {seen!r}"
    data = json.loads(map_path.read_text(encoding="utf-8"))
    assert data == {
        S78W2_LANE_A: S78W2_URL_MAP,
        S78W2_LANE_B: S78W2_URL_MAP,
    }, f"the map was not emitted for the season's lanes: {data!r}"


def test_s78w2_map_verb_nonzero_check_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """rc nonzero: the verb exits nonzero and the map file is untouched.

    Two arms: an absent map stays absent; a seeded map keeps its
    entries byte-identical. The check still ran (one gh call naming
    the url) -- the gate is what refuses the write.
    """
    from rumpun import cli as cli_module

    root = _s78w2_campaign(tmp_path, name="s78w2verbrc")
    _s78w2_sealed(root)
    map_path = root / board.BOARD_MAP_FILE
    _s78w2_seed_map(root, {S78W2_LANE_OTHER: S78W2_URL_SURVIVOR})
    seeded = map_path.read_bytes()
    monkeypatch.chdir(root.parent)
    seen = _s78w2_fake_check(monkeypatch, rc=1)
    rc = cli_module.main(["board", "--map", "s78f", S78W2_URL_MAP])
    assert rc != 0, "a failed issue check did not gate the write"
    assert len(seen) == 1, f"the check must be exactly one call: {seen!r}"
    assert S78W2_URL_MAP in seen[0], "the check did not name the issue url"
    assert map_path.read_bytes() == seeded, "a failed check still wrote the map"


def test_s78w2_dry_run_names_issue_1_and_the_sealed_record(tmp_path: Path) -> None:
    """Map-fed dry run: the render names issue #1 and the sealed record.

    The expected bytes are constructed inline (not via render_sync), so
    the pin is independent of the implementation's renderer. boom seams
    prove nothing live is consulted; the tree and ledger stay put.
    """
    root = _s78w2_campaign(tmp_path, name="s78w2dry")
    record_path = _s78w2_sealed(root)
    _s78w2_seed_map(
        root,
        {S78W2_LANE_A: S78W2_URL_ISSUE1, S78W2_LANE_B: S78W2_URL_ISSUE1},
    )
    before = _s78w2_tree_bytes(root)

    def boom(*args: object) -> None:
        raise AssertionError("the dry run must not call pickup or run")

    rendered = board.sync_season(
        root, "s78f", dry_run=True, pickup_fn=boom, run=boom  # type: ignore[arg-type]
    )
    expected = "\n".join(
        [
            "board sync s78f (dry-run): nothing written",
            f"comment {S78W2_URL_ISSUE1} with {record_path} (verbatim, sealed)",
            f"close {S78W2_URL_ISSUE1}",
        ]
    )
    assert rendered == expected, f"render mismatch:\n{rendered!r}\n!=\n{expected!r}"
    assert _s78w2_tree_bytes(root) == before, "the dry run wrote files"
    assert list(akar.declared_ids(root)) == ["s78f-harvest"], (
        "the dry run wrote records"
    )


def test_s78w2_cli_dry_run_exits_zero_writing_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`board --sync s78f --dry-run`: rc 0, the exact render on stdout.

    The map is seeded and a boom pickup proves the map-first wiring end
    to end through the CLI: if the lookup fell through to the live
    pickup, the boom fires. One readouterr() snapshot holds both
    streams (readouterr drains per call).
    """
    from rumpun import cli as cli_module

    root = _s78w2_campaign(tmp_path, name="s78w2clidx")
    record_path = _s78w2_sealed(root)
    _s78w2_seed_map(root, {S78W2_LANE_A: S78W2_URL_ISSUE1})

    def boom(*args: object) -> list[dict[str, str]]:
        raise AssertionError("the CLI dry run must not call pickup (map hit)")

    monkeypatch.setattr(board, "pickup", boom)
    monkeypatch.chdir(root.parent)
    before = _s78w2_tree_bytes(root)
    rc = cli_module.main(["board", "--sync", "s78f", "--dry-run"])
    assert rc == 0, "the CLI dry run did not exit 0"
    expected = (
        "board sync s78f (dry-run): nothing written\n"
        f"comment {S78W2_URL_ISSUE1} with {record_path} (verbatim, sealed)\n"
        f"close {S78W2_URL_ISSUE1}\n"
    )
    assert capsys.readouterr().out == expected, "stdout is not the exact render"
    assert _s78w2_tree_bytes(root) == before, "the CLI dry run wrote files"
