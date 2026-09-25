"""s79 w2 pins — the first board-pulled close: the loop's proof, offline.

Spec source: .rumpun/runs/s79/w2/prompt.md. Precedents: the s78 w1 pins
(campaign fixtures, the boomed sync seams, the inline render), the s45
rename pins (their pin 8 is red-until-fixed -- the same shape as the
repro pin here). Offline: these pins make no gh call -- sync runs on the
boomed pickup_fn/run seams, the map is a seeded file, and the repro pin
reads lint's resolver directly. The one live read sits outside the pins:
`gh issue view 2 -R khursanirevo/rumpun`, captured verbatim at
.rumpun/runs/s79/w2/issue2.txt -- its repro steps are pin 3's spec.

Contract these pins hold -- src/rumpun/board.py, src/rumpun/akar.py,
src/rumpun/lint.py:

1. sync_season --dry-run over a fixture campaign whose map names issue
   #2 and whose sealed harvest record exists: the render carries the
   issue url on the comment and close lines, the record it names holds
   the sealed body byte-for-byte (four header lines, the body, the
   sha256 footer), the comment argv hands the record file to gh as the
   verbatim body, and the dry run writes nothing.
2. The full-loop composition, one test: emit_lane_map ->
   issue_for_season -> sync_season --dry-run, each stage consuming the
   previous stage's return (no re-derivation), pickup and run boomed so
   nothing live is consulted, and the dry run writes nothing.
3. The issue #2 repro pin (red-shaped until w1's fix lands): append a
   record the way a user does after `rumpun init` -- project root, not
   .rumpun -- build the scaffold-documented `ledger:<id>@<sha256>`
   citation from the emitted record bytes, and assert it resolves where
   lint scans (the .rumpun root). Until append_record's emission and
   the resolver agree, this pin fails naming the divergence.
4. GREEN GUARD: the campaign-convention append (root = .rumpun) keeps
   resolving -- the well-formed path w1's fix must not disturb.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import pytest

from rumpun import akar, lint

logger = logging.getLogger(__name__)

S79W2_SID = "s79f"
S79W2_ISSUE2_URL = "https://github.com/khursanirevo/rumpun/issues/2"

S79W2_LANE_A = "s79-loop-a"
S79W2_LANE_B = "s79-loop-b"

S79W2_SEASON_YAML = """\
id: s79f
parent: s79
goal: fixture season for the s79 w2 board-loop pins
metric: modules_integrated
writers:
  - name: w1
    lane: s79-loop-a
  - name: w2
    lane: s79-loop-b
"""

S79W2_HARVEST_BODY = (
    "season s79f: completed\n"
    "duration: 60s\n"
    "\n"
    "| agent | route | state | exit_code | seconds |\n"
    "|---|---|---|---|---|\n"
    "| w1 | fable | exited | 0 | 60.0 |\n"
    "| w2 | fable | exited | 0 | 60.0 |\n"
    "\n"
    "verdict: WIN\n"
    "implies: the first board-pulled close holds offline\n"
)

S79W2_DOC_BODY = "the s79 w2 repro: appended here, resolved where lint scans\n"


def _s79w2_board_module():
    """Import rumpun.board; fail naming the spec reason when unlanded."""
    try:
        from rumpun import board as board_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/board.py missing/unimportable: {exc}")
    return board_module


def _s79w2_campaign(tmp_path: Path) -> Path:
    """A fresh .rumpun root: rumpun.yaml + the fixture season s79f.

    The season yaml declares two writers whose lanes are the map keys
    (s79-loop-a, s79-loop-b); the ledger starts empty.
    """
    campaign = tmp_path / "s79w2proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        "autonomy:\n  stage: manual\n", encoding="utf-8"
    )
    (root / "seasons" / f"{S79W2_SID}.yaml").write_text(
        S79W2_SEASON_YAML, encoding="utf-8"
    )
    return root


def _s79w2_sealed_harvest(root: Path) -> Path:
    """Append the s79f-harvest record through akar itself, so the seal is real."""
    return akar.append_record(
        root, f"{S79W2_SID}-harvest", f"season {S79W2_SID} harvest", S79W2_HARVEST_BODY
    )


def _s79w2_map(root: Path, payload: dict[str, str]) -> None:
    """Seed the fixture lane map with the exact sync-contract shape."""
    (root / "board-map.json").write_text(
        json.dumps(payload) + "\n", encoding="utf-8"
    )


def _s79w2_tree_bytes(root: Path) -> dict[str, bytes]:
    """Every file under root as {relative path: bytes}, for write-nothing pins."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _s79w2_record_body(record_path: Path) -> str:
    """The recoverable record body: lines[4:-1] joined (the akar layout)."""
    lines = record_path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[4:-1])


def _s79w2_citation_of(record_path: Path) -> str:
    """The ledger:<id>@<digest> citation the emitted record bytes support.

    Derived from what akar.append_record actually wrote (the first id
    line and the trailing sha256 footer), so w1's emission fix keeps
    this pin honest about the form the merged tree emits.
    """
    lines = record_path.read_text(encoding="utf-8").splitlines()
    rid = next(
        line.removeprefix("id: ").strip()
        for line in lines
        if line.startswith("id: ")
    )
    footer = lines[-1]
    if not footer.startswith("sha256: "):
        pytest.fail(
            f"{record_path} does not end in a sha256 footer; the emitted "
            f"citation form changed, re-derive this pin's builder: {footer!r}"
        )
    return f"ledger:{rid}@{footer.removeprefix('sha256: ')}"


def test_s79w2_sync_dry_run_renders_the_mapped_close_offline(tmp_path: Path) -> None:
    """The mapped close, offline: render, verbatim body, argv, writes nothing.

    The map names issue #2 for both lanes; the sealed s79f-harvest
    exists; pickup_fn and run boom -- the dry run must consult nothing
    live, write nothing, and render exactly the plan: comment the
    record file onto issue #2 verbatim, then close it.
    """
    board = _s79w2_board_module()
    root = _s79w2_campaign(tmp_path)
    record_path = _s79w2_sealed_harvest(root)
    _s79w2_map(root, {S79W2_LANE_A: S79W2_ISSUE2_URL, S79W2_LANE_B: S79W2_ISSUE2_URL})
    before = _s79w2_tree_bytes(root)

    def boom(*args: object) -> None:
        raise AssertionError("the seeded map must make sync skip pickup/run")

    rendered = board.sync_season(
        root, S79W2_SID, dry_run=True, pickup_fn=boom, run=boom  # type: ignore[arg-type]
    )
    expected = "\n".join(
        [
            f"board sync {S79W2_SID} (dry-run): nothing written",
            f"comment {S79W2_ISSUE2_URL} with {record_path} (verbatim, sealed)",
            f"close {S79W2_ISSUE2_URL}",
        ]
    )
    assert rendered == expected, f"render mismatch:\n{rendered!r}\n!=\n{expected!r}"
    assert _s79w2_record_body(record_path) == S79W2_HARVEST_BODY, (
        "the record the render names must carry the sealed body byte-for-byte"
    )
    digest = hashlib.sha256(S79W2_HARVEST_BODY.encode("utf-8")).hexdigest()
    footer = record_path.read_text(encoding="utf-8").splitlines()[-1]
    assert footer == f"sha256: {digest}", "the record's sha256 seal is not real"
    assert board.harvest_comment_argv(S79W2_ISSUE2_URL, record_path) == [
        "gh",
        "issue",
        "comment",
        S79W2_ISSUE2_URL,
        "--body-file",
        str(record_path),
    ], "the planned comment argv must hand gh the record file itself"
    assert _s79w2_tree_bytes(root) == before, "the dry run wrote files"


def test_s79w2_full_loop_composes_map_lookup_and_dry_run(tmp_path: Path) -> None:
    """emit_lane_map -> issue_for_season -> sync --dry-run, chained, offline.

    Each stage consumes the previous stage's return: the emitted map
    (not a re-derived dict), the url the lookup returns (not a loaded
    map read), the record the append returned. pickup/run boom, so the
    composition proves the s78 helpers close the loop with nothing live.
    """
    board = _s79w2_board_module()
    root = _s79w2_campaign(tmp_path)
    record_path = _s79w2_sealed_harvest(root)

    def boom(*args: object) -> None:
        raise AssertionError("the emitted map must satisfy lookup and sync offline")

    merged = board.emit_lane_map(root, S79W2_SID, S79W2_ISSUE2_URL)
    assert merged == {S79W2_LANE_A: S79W2_ISSUE2_URL, S79W2_LANE_B: S79W2_ISSUE2_URL}
    url = board.issue_for_season(root, S79W2_SID, pickup_fn=boom)  # type: ignore[arg-type]
    assert url == S79W2_ISSUE2_URL, "the lookup must resolve through the emitted map"
    before = _s79w2_tree_bytes(root)
    rendered = board.sync_season(
        root, S79W2_SID, dry_run=True, pickup_fn=boom, run=boom  # type: ignore[arg-type]
    )
    expected = "\n".join(
        [
            f"board sync {S79W2_SID} (dry-run): nothing written",
            f"comment {url} with {record_path} (verbatim, sealed)",
            f"close {url}",
        ]
    )
    assert rendered == expected, f"render mismatch:\n{rendered!r}\n!=\n{expected!r}"
    assert _s79w2_tree_bytes(root) == before, "the dry-run stages wrote files"


def test_s79w2_appended_record_citation_resolves_where_lint_scans(
    tmp_path: Path,
) -> None:
    """The issue #2 repro (red-shaped until w1's fix lands).

    The repro, followed step by step from .rumpun/runs/s79/w2/issue2.txt:
    `rumpun init` scaffolds .rumpun/ledger/; the user appends a record via
    akar.append_record with the PROJECT root (the natural call, per the
    issue's step 2); the citation built from the emitted record bytes must
    resolve where lint scans -- the .rumpun root. RED today: the record
    lands at <project>/ledger/ (paths.ledger_new(root) = root/"ledger")
    while the resolver scans .rumpun/ledger/, so find_record misses and
    _citation_resolves returns False. GREEN once w1's fix makes the
    emitted form resolve; the citation stays derived from the emitted
    bytes, so the pin holds whichever form the merged tree emits.
    """
    proj = tmp_path / "s79w2user"
    (proj / ".rumpun" / "ledger").mkdir(parents=True)  # what rumpun init scaffolds
    record_path = akar.append_record(
        proj, "s79w2-doc", "s79 w2 repro fixture", S79W2_DOC_BODY
    )
    assert record_path.is_file(), "append_record returned a path it did not write"
    citation = _s79w2_citation_of(record_path)
    assert lint._citation_resolves(citation, proj / ".rumpun") is True, (
        f"the appended record's citation {citation} does not resolve where "
        f"lint scans: record emitted at {record_path}, resolver rooted at "
        f"{proj / '.rumpun'} (the issue #2 divergence)"
    )


def test_s79w2_campaign_append_citation_resolves_green_guard(tmp_path: Path) -> None:
    """GREEN GUARD: the campaign-convention append resolves today, and must stay.

    The campaign harness appends with root = .rumpun (every ledger record
    in this repo lives there), so its citations resolve. w1's fix must
    not disturb this well-formed path.
    """
    camp = tmp_path / "s79w2camp" / ".rumpun"
    record_path = akar.append_record(
        camp, "s79w2-doc-camp", "s79 w2 green guard", S79W2_DOC_BODY
    )
    assert record_path.is_file(), "append_record returned a path it did not write"
    citation = _s79w2_citation_of(record_path)
    assert lint._citation_resolves(citation, camp) is True, (
        f"the campaign-convention citation {citation} stopped resolving; "
        "w1's fix broke the well-formed path"
    )
