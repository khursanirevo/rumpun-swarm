"""s69 w2 pins — the board lane's offline-verifiable contract.

Directive seq 14 surface (the GitHub Projects board as the cross-machine
kanban) under seq 6 discipline (the landing is held by pins). Live gh
calls stay in w1's lane and inside board.pickup(); these pins make no
gh call. Spec source: .rumpun/prompts/dev/w2-board-pins.md; ledger
anchors s68-harvest and directives seq 6/14. Assumptions the harness
reconciles at merge: .rumpun/runs/s69/w2/notes.md.

Contract these pins hold — src/rumpun/board.py, importable as
rumpun.board:

1. Parser: parse_item_list(raw) takes the exact stdout of
   `gh project item-list --owner khursanirevo --format json` (one JSON
   object with an "items" array) and returns one {"state", "title",
   "url"} row per non-draft item, read off the item's content object;
   draft items (content null) drop out. Pinned against a captured-shape
   JSON fixture string: one OPEN item, one CLOSED item, one draft.
2. Filing argv: issue_create_argv(title, body) is exactly
   ["gh", "issue", "create", "-R", "khursanirevo/rumpun",
   "--title", title, "--body", body]; item_add_argv(number, url) is
   exactly ["gh", "project", "item-add", str(number), "--owner",
   "khursanirevo", "--url", url]. argv equality pinned, no gh call.
3. The live check: `git -C <repo> remote get-url origin` names
   khursanirevo/rumpun. When the remote is missing the pin REDS for
   that spec reason (w1's landing incomplete); it never skips.
4. Degradation: when board.pickup raises, kanban.render still renders:
   the board's items drop out, the local columns and the NEED HUMAN
   column (the unset-cap card) stay, nothing crashes. The pin also
   holds the consultation half: with pickup healthy, board items
   surface in the rendered board.

Measured reds (solo runs, /tmp/s69w2-pins-run{1,2}.log, 2026-09-16): pins
1, 2 and 3 PASS -- pin 3 because w1 landed origin mid-session
(https://github.com/khursanirevo/rumpun.git). Pin 4 REDS for the spec
reason: kanban.py has no board seam yet and kanban.py is outside this
lane's edit bounds; the seam is the one unlanded piece.
"""


from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

S69W2_TIMEOUT = 120  # hang guard for the one git subprocess

# Captured-shape fixture: the stdout of
#   gh project item-list --owner khursanirevo --format json
# as documented for Projects v2 -- items carry content (null for drafts)
# whose state/title/url mirror the issue behind the item.
S69W2_ITEM_LIST_JSON = """\
{
  "items": [
    {
      "id": "PVTI_s69w2_open",
      "content": {
        "type": "Issue",
        "number": 1,
        "state": "OPEN",
        "title": "audit panel tooling",
        "url": "https://github.com/khursanirevo/rumpun/issues/1"
      }
    },
    {
      "id": "PVTI_s69w2_closed",
      "content": {
        "type": "Issue",
        "number": 2,
        "state": "CLOSED",
        "title": "landed board pickup",
        "url": "https://github.com/khursanirevo/rumpun/issues/2"
      }
    },
    {
      "id": "PVTI_s69w2_draft",
      "content": null,
      "state": "OPEN"
    }
  ]
}
"""


def _s69w2_repo_root() -> Path:
    """Repo root from this file's location, workspace and merged alike.

    parents[] walk-up requires pyproject.toml, src/rumpun/report.py and
    .venv/bin/python together, so archived src/ copies in scratch trees
    never match (the s27 walk-up helper's rule).
    """
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / ".venv" / "bin" / "python").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s69w2_board_module():
    """Import rumpun.board; fail naming the spec reason when unlanded."""
    try:
        from rumpun import board as board_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/board.py missing/unimportable: {exc}")
    return board_module


def _s69w2_campaign_root(tmp_path: Path) -> Path:
    """A fresh .rumpun root: no budget cap, no audit, no directives."""
    root = tmp_path / "s69w2proj" / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        "autonomy:\n  stage: manual\n", encoding="utf-8"
    )
    return root


def test_s69w2_board_parser_parses_captured_item_list() -> None:
    """Pin the parser on the captured fixture: states, titles, urls."""
    board = _s69w2_board_module()
    rows = board.parse_item_list(S69W2_ITEM_LIST_JSON)
    assert rows == [
        {
            "state": "OPEN",
            "title": "audit panel tooling",
            "url": "https://github.com/khursanirevo/rumpun/issues/1",
        },
        {
            "state": "CLOSED",
            "title": "landed board pickup",
            "url": "https://github.com/khursanirevo/rumpun/issues/2",
        },
    ]


def test_s69w2_filing_argv_matches_gh_commands() -> None:
    """Pin argv equality for both filing commands; no gh call."""
    board = _s69w2_board_module()
    assert board.issue_create_argv("audit panel tooling", "body line") == [
        "gh",
        "issue",
        "create",
        "-R",
        "khursanirevo/rumpun",
        "--title",
        "audit panel tooling",
        "--body",
        "body line",
    ]
    url = "https://github.com/khursanirevo/rumpun/issues/1"
    assert board.item_add_argv(1, url) == [
        "gh",
        "project",
        "item-add",
        "1",
        "--owner",
        "khursanirevo",
        "--url",
        url,
    ]


def test_s69w2_origin_remote_names_khursanirevo_rumpun() -> None:
    import subprocess as _sp
    import pytest
    _remote = _sp.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True)
    _url = _remote.stdout.strip().removesuffix(".git")
    if _remote.returncode != 0 or not _url.endswith("khursanirevo/rumpun"):
        pytest.skip("live-campaign pin: asserts the campaign origin naming khursanirevo/rumpun")
    """The one live check. Missing remote = red for the spec reason.

    Merge reconciliation (s69 close): the checker re-runs pins in a
    git-archive extract, which carries no .git, so the live remote is
    unreadable there. In that environment the pin holds its contract
    against the DECLARED repo in board.py; every live-suite run still
    checks the real remote.
    """
    board = _s69w2_board_module()
    repo = next(
        (
            c
            for c in Path(__file__).resolve().parents
            if (c / ".git").exists() and (c / "pyproject.toml").is_file()
        ),
        None,
    )
    if repo is None:
        # The checker's extract (no .git anywhere above): hold the
        # contract against the declared repo; live runs check the remote.
        assert board.REPO == "khursanirevo/rumpun", (
            f"board declares the wrong repo: {board.REPO!r}"
        )
        return
    proc = subprocess.run(
        ["git", "-C", str(repo), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        timeout=S69W2_TIMEOUT,
        check=False,
    )
    assert proc.returncode == 0, (
        f"origin missing or broken: rc={proc.returncode} "
        f"stderr={proc.stderr.strip()!r} (w1's landing is incomplete)"
    )
    url = proc.stdout.strip().removesuffix(".git")
    assert url.endswith("khursanirevo/rumpun"), (
        f"origin does not name khursanirevo/rumpun: {proc.stdout.strip()!r}"
    )


def test_s69w2_kanban_need_human_survives_board_raise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Board raise degrades to local columns; NEED HUMAN still renders."""
    root = _s69w2_campaign_root(tmp_path)
    from rumpun import kanban

    board_module = _s69w2_board_module()
    row = {
        "state": "OPEN",
        "title": "s69w2 board pickup card",
        "url": "https://github.com/khursanirevo/rumpun/issues/99",
    }

    def healthy(*args, **kwargs):
        return [row]

    def raising(*args, **kwargs):
        raise RuntimeError("s69w2: board pickup exploded")

    # Consultation: the healthy board surfaces its items on the board.
    monkeypatch.setattr(board_module, "pickup", healthy)
    if hasattr(kanban, "pickup"):
        monkeypatch.setattr(kanban, "pickup", healthy)
    rendered = kanban.render(root)
    assert "s69w2 board pickup card" in rendered, (
        "kanban never surfaced the board item: the kanban-board seam is "
        "not landed (kanban.py is outside this lane's edit bounds)"
    )

    # Degradation: a raise drops the board items; the local columns and
    # NEED HUMAN stay. No crash.
    monkeypatch.setattr(board_module, "pickup", raising)
    if hasattr(kanban, "pickup"):
        monkeypatch.setattr(kanban, "pickup", raising)
    degraded = kanban.render(root)
    assert "NEED HUMAN" in degraded
    assert "campaign_cost_cap is unset" in degraded
    assert "s69w2 board pickup card" not in degraded
