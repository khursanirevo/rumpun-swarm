"""s76 w2 pins — the audit-to-board feed's offline-verifiable contract.

Spec source: .rumpun/runs/s76/w2/prompt.md (the s76 w2 brief). The w1
lane files the candidates live (issues #3/#4 mid-flight at write time);
these pins hold the feed's shape offline: no gh call, no .rumpun state
edits, the live evidence stays in w1's notes.md.

Contract these pins hold -- src/rumpun/board.py:

1. candidates_from_audit(record_path): the verbatim candidate texts of
   an audit record, in record order, under the s66 convention -- a
   candidate is a line starting exactly "candidate: ", its text the
   stripped rest of the line (the kanban backlog reads the same way).
   Pure read: no seal gate, no dedupe. The record's other lines never
   extract -- findings lines, the "candidate cap" line that names
   candidates without carrying the prefix, the sha256 footer. A missing
   file raises OSError (an honest read, not a silent []).
2. audit_issue_argv(candidate, citation): the exact argv filing one
   candidate as a repo issue --
   ["gh", "issue", "create", "-R", "khursanirevo/rumpun",
    "--title", title, "--body", body]
   title: the candidate whitespace-collapsed, and when that runs over
   60 chars truncated to the first 57 + "..." -- deterministic, same
   input same argv, <=60 always. body: the candidate verbatim +
   "\n\ncitation: " + citation.
3. sync_season --dry-run against a fixture campaign + fixture pickup
   rows (no map): the fallback lane-title match feeds the render; the
   render names the matched issue; the comment line names the sealed
   record file whose bytes carry the body + sha256 footer -- what
   --body-file delivers verbatim; the dry run writes nothing and calls
   nothing live.
4. The real --sync outcome shape, record/exit only: through the CLI
   (board --sync SID, bounded seam monkeypatched, map hit) the exit is
   0 and stdout is the exact live receipt; a refusing sync (unmapped
   season, empty fallback) exits 1 via main's BoardError arm, never a
   silent 0. No live gh call in pins; w1's notes.md is the live
   evidence.
"""


from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

S76W2_URL_A = "https://github.com/khursanirevo/rumpun/issues/801"
S76W2_URL_B = "https://github.com/khursanirevo/rumpun/issues/802"
S76W2_URL_UNRELATED = "https://github.com/khursanirevo/rumpun/issues/803"
S76W2_LANE_A = "lane-s76w2-a"
S76W2_LANE_B = "lane-s76w2-b"

S76W2_SEASON_YAML = """\
id: s76f
parent: s76
goal: fixture season for the s76 w2 audit-to-board feed pins
metric: modules_integrated
writers:
  - name: w1
    lane: lane-s76w2-a
  - name: w2
    lane: lane-s76w2-b
"""

S76W2_AUDIT_BODY = (
    "scope: s62..s71 (9 engine seasons)\n"
    "F3 verdict histogram: 8 WIN (1 salvaged), 0 LOSS, 0 INVALID, other 1\n"
    "candidate: usefulness residual: independent artifact checks remain "
    "absent (usefulness-decade-1)\n"
    "candidate: usefulness residual: the ledger establishes 24 WIN, eight "
    "LOSS, two missing (usefulness-decade-1)\n"
    "candidate cap 3 reached in pipeline order; also triggered but "
    "unproposed here: residual x3\n"
    "candidate: usefulness residual: recorded verdicts do not "
    "independently establish correctness (usefulness-decade-1)\n"
)

S76W2_CANDIDATES = [
    (
        "usefulness residual: independent artifact checks remain absent "
        "(usefulness-decade-1)"
    ),
    (
        "usefulness residual: the ledger establishes 24 WIN, eight LOSS, "
        "two missing (usefulness-decade-1)"
    ),
    (
        "usefulness residual: recorded verdicts do not independently "
        "establish correctness (usefulness-decade-1)"
    ),
]

S76W2_HARVEST_BODY = (
    "season s76f: completed\n"
    "duration: 60s\n"
    "\n"
    "| agent | route | state | exit_code | seconds |\n"
    "|---|---|---|---|---|\n"
    "| w1 | fable | exited | 0 | 60.0 |\n"
    "\n"
    "verdict: WIN\n"
    "implies: the feed pins hold offline\n"
)


def _s76w2_board_module():
    """Import rumpun.board; fail naming the spec reason when unlanded."""
    try:
        from rumpun import board as board_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/board.py missing/unimportable: {exc}")
    return board_module


def _s76w2_campaign(tmp_path: Path) -> Path:
    """A fresh .rumpun root: rumpun.yaml + the fixture season s76f.

    The season declares two writers whose lanes are the fixture keys
    (lane-s76w2-a, lane-s76w2-b); the ledger starts empty and no
    board-map.json exists, so every issue match below runs the fallback.
    """
    campaign = tmp_path / "s76w2proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        "autonomy:\n  stage: manual\n", encoding="utf-8"
    )
    (root / "seasons" / "s76f.yaml").write_text(S76W2_SEASON_YAML, encoding="utf-8")
    return root


def _s76w2_sealed(root: Path, record_id: str, title: str, body: str) -> Path:
    """Append the record through akar itself, so the sha256 seal is real."""
    from rumpun import akar

    return akar.append_record(root, record_id, title, body)


def _s76w2_tree_bytes(root: Path) -> dict[str, bytes]:
    """Every file under root as {relative path: bytes}, for write-nothing pins."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_s76w2_candidates_from_a_sealed_audit_record(tmp_path: Path) -> None:
    """The sealed fixture record's candidate lines extract verbatim, in order.

    The record is sealed through akar itself; the findings lines, the
    "candidate cap" line (names candidates without carrying the
    "candidate: " prefix), and the sha256 footer never extract.
    """
    board = _s76w2_board_module()
    root = _s76w2_campaign(tmp_path)
    record = _s76w2_sealed(root, "audit-43", "reflection audit", S76W2_AUDIT_BODY)
    text = record.read_text(encoding="utf-8")
    assert "sha256: " in text, "the fixture record must be sealed"
    assert board.candidates_from_audit(record) == S76W2_CANDIDATES


def test_s76w2_candidates_from_audit_is_a_pure_read(tmp_path: Path) -> None:
    """No seal gate, no dedupe: an unsealed file reads; none -> []; missing -> OSError."""
    board = _s76w2_board_module()
    plain = tmp_path / "plain.md"
    plain.write_text("candidate: alpha\ncandidate: alpha\n", encoding="utf-8")
    assert board.candidates_from_audit(plain) == ["alpha", "alpha"]
    empty = tmp_path / "empty.md"
    empty.write_text("no candidates armed here\n", encoding="utf-8")
    assert board.candidates_from_audit(empty) == []
    with pytest.raises(OSError):
        board.candidates_from_audit(tmp_path / "missing.md")


def test_s76w2_audit_issue_argv_is_exact() -> None:
    """A short candidate files with its text as the title, uncapped.

    The expected argv is constructed literally (builder-independent).
    """
    board = _s76w2_board_module()
    candidate = "independent artifact checks remain absent"
    argv = board.audit_issue_argv(candidate, "audit-43")
    assert argv == [
        "gh",
        "issue",
        "create",
        "-R",
        "khursanirevo/rumpun",
        "--title",
        "independent artifact checks remain absent",
        "--body",
        candidate + "\n\ncitation: audit-43",
    ]


def test_s76w2_audit_issue_title_compresses_deterministically() -> None:
    """Over 60 collapsed chars the title truncates to the first 57 + '...'.

    The body keeps the candidate verbatim (newlines included); the same
    input yields the same argv; the 60/61 boundary flips exactly there.
    """
    board = _s76w2_board_module()
    long_candidate = (
        "usefulness residual: recorded verdicts do not independently "
        "establish\nimplementation correctness or practical value\n"
        "(usefulness-decade-1)"
    )
    collapsed = " ".join(long_candidate.split())
    expected_title = collapsed[:57] + "..."
    assert len(expected_title) == 60
    argv = board.audit_issue_argv(long_candidate, "audit-43")
    assert argv == [
        "gh",
        "issue",
        "create",
        "-R",
        "khursanirevo/rumpun",
        "--title",
        expected_title,
        "--body",
        long_candidate + "\n\ncitation: audit-43",
    ]
    assert board.audit_issue_argv(long_candidate, "audit-43") == argv, (
        "same input must give the same argv"
    )
    at_cap = board.audit_issue_argv("x" * 60, "audit-43")
    assert at_cap[6] == "x" * 60, "60 collapsed chars stay uncapped"
    one_over = board.audit_issue_argv("x" * 61, "audit-43")
    assert one_over[6] == "x" * 57 + "...", "61 collapsed chars truncate"


def test_s76w2_sync_dry_run_renders_the_pickup_matched_issue(tmp_path: Path) -> None:
    """--dry-run on fixture pickup rows (no map): render names the issue.

    The rows carry lane B before lane A so the fallback's board-order
    rule decides; the expected render is constructed inline (not via
    render_sync). The comment line names the sealed record file whose
    bytes carry the harvest text + sha256 footer -- the body --body-file
    delivers verbatim. Tree bytes and the ledger stay untouched, and the
    boom seams prove nothing live runs.
    """
    board = _s76w2_board_module()
    root = _s76w2_campaign(tmp_path)
    record_path = _s76w2_sealed(
        root, "s76f-harvest", "season s76f harvest", S76W2_HARVEST_BODY
    )
    before = _s76w2_tree_bytes(root)

    def rows() -> list[dict[str, str]]:
        return [
            {"state": "OPEN", "title": "unrelated", "url": S76W2_URL_UNRELATED},
            {"state": "OPEN", "title": S76W2_LANE_B, "url": S76W2_URL_B},
            {"state": "OPEN", "title": S76W2_LANE_A, "url": S76W2_URL_A},
        ]

    def boom(*args: object) -> None:
        raise AssertionError("the dry run must not call pickup or run")

    rendered = board.sync_season(
        root, "s76f", dry_run=True, pickup_fn=rows, run=boom  # type: ignore[arg-type]
    )
    expected = "\n".join(
        [
            "board sync s76f (dry-run): nothing written",
            f"comment {S76W2_URL_B} with {record_path} (verbatim, sealed)",
            f"close {S76W2_URL_B}",
        ]
    )
    assert rendered == expected, f"render mismatch:\n{rendered!r}\n!=\n{expected!r}"
    sealed_text = record_path.read_text(encoding="utf-8")
    assert "verdict: WIN" in sealed_text, "the record must carry the harvest body"
    assert "sha256: " in sealed_text, "the record must carry its sha256 seal"
    assert _s76w2_tree_bytes(root) == before, "the dry run wrote files"
    from rumpun import akar

    assert list(akar.declared_ids(root)) == ["s76f-harvest"], "the dry run wrote records"


def test_s76w2_cli_live_sync_exits_zero_with_the_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The real --sync outcome shape: receipt on stdout, exit 0, no writes.

    The bounded seam is monkeypatched (the CLI cannot inject run=), the
    map hit routes the match, and a boom pickup proves no network. The
    receipt is the exact live render; the seam saw comment then close
    with the builder argv.
    """
    board = _s76w2_board_module()
    root = _s76w2_campaign(tmp_path)
    record_path = _s76w2_sealed(
        root, "s76f-harvest", "season s76f harvest", S76W2_HARVEST_BODY
    )
    (root / "board-map.json").write_text(
        json.dumps({S76W2_LANE_A: S76W2_URL_A}) + "\n", encoding="utf-8"
    )
    from rumpun import cli as cli_module

    seen: list[list[str]] = []

    def fake_run(argv: list[str]) -> None:
        seen.append(argv)

    def boom(*args: object) -> list[dict[str, str]]:
        raise AssertionError("the CLI sync must not call pickup (map hit)")

    monkeypatch.setattr(board, "_bounded_run", fake_run)
    monkeypatch.setattr(board, "pickup", boom)
    monkeypatch.chdir(root.parent)
    before = _s76w2_tree_bytes(root)
    rc = cli_module.main(["board", "--sync", "s76f"])
    assert rc == 0, "the live CLI sync did not exit 0"
    expected = (
        "board sync s76f: commented and closed\n"
        f"comment {S76W2_URL_A} with {record_path} (verbatim, sealed)\n"
        f"close {S76W2_URL_A}\n"
    )
    assert capsys.readouterr().out == expected, "stdout is not the exact receipt"
    assert seen == [
        ["gh", "issue", "comment", S76W2_URL_A, "--body-file", str(record_path)],
        ["gh", "issue", "close", S76W2_URL_A],
    ], f"the bounded seam saw: {seen!r}"
    assert _s76w2_tree_bytes(root) == before, "the live CLI sync wrote files"


def test_s76w2_refusing_sync_exits_one_not_silent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A refusing sync (unmapped season) exits 1 via main's BoardError arm.

    pickup returns [] offline (empty board fallback), so the unmapped
    refusal fires before any gh call. One readouterr() snapshot holds
    both streams (readouterr drains; a second call reads an empty
    buffer), and caplog is unusable here: the CLI's _setup_logging uses
    force=True, which strips caplog's root handler mid-test.
    """
    board = _s76w2_board_module()
    root = _s76w2_campaign(tmp_path)
    _s76w2_sealed(root, "s76f-harvest", "season s76f harvest", S76W2_HARVEST_BODY)
    from rumpun import cli as cli_module

    monkeypatch.setattr(board, "pickup", lambda *args: [])
    monkeypatch.chdir(root.parent)
    before = _s76w2_tree_bytes(root)
    rc = cli_module.main(["board", "--sync", "s76f"])
    assert rc == 1, "the refusing sync did not exit 1"
    captured = capsys.readouterr()
    assert captured.out == "", "a refusal printed a success receipt"
    assert "unmapped" in captured.err, "the refusal did not name the reason"
    assert _s76w2_tree_bytes(root) == before, "the refusing sync wrote files"
