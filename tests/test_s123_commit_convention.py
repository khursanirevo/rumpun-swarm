"""s123 w1 pins -- the lane-commit rule codified; the plan prefers the loop draft.

Spec source: the s123 w1 brief, codifying two incidents: s114 w2 (78ed003)
and s122 w1 (ef4a78d) both committed exactly their bounded files with
season-tagged subjects before anyone wrote the rule down. The rule lands in
two operator surfaces, and the planner learns the loop's draft hand-off:

- the lane-commit rule: a writer may commit exactly its bounded files,
  subject <= 50 chars, season-tagged; the close worker folds the rest.
  Stated in docs/campaign-guide.md (the close section) and the README
  lifecycle section.
- the planner (src/rumpun/evolve.py draft_next, the verb behind
  `rumpun evolve plan`) warns at plan time when the loop's draft exists for
  the next id -- runs/<parent>/seasons/<next>.yaml, the s120/s122
  close-prep hand-off -- naming its path; the worker fills that draft
  instead of a fresh one. The s116 warning pattern is the house style: the
  hint rides the plan, it never blocks the draft.

Offline: in-process over tmp_path fixture campaigns; the tmp campaign
ledger is never the real one, and no season runs.

Grafting: drop this file into tests/. Helpers and constants carry the
_s123 prefix; nothing collides with existing defs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from rumpun import evolve

REPO = Path(__file__).resolve().parents[1]
GUIDE = REPO / "docs" / "campaign-guide.md"
README = REPO / "README.md"

# the lane-commit rule's tokens, asserted on both operator surfaces
_S123_RULE_TOKENS = (
    "lane-commit rule",
    "bounded files",
    "50 chars",
    "season-tagged",
    "folds the rest",
)


def _s123_norm(text: str) -> str:
    """The text with runs of whitespace collapsed to single spaces.

    Doc pins match against this shape: the rule must read as a statement,
    not as a particular line wrap, so a rewrap never breaks the pin.
    """
    return " ".join(text.split())


def _s123_season_text(sid: str) -> str:
    """One draftable season: id, goal, methodology with pipeline, no parent.

    No parent line keeps the s116 assessment walk silent (drought 1 < the
    cadence 6), so the planner pins read only the loop-draft hint.
    """
    return (
        f"id: {sid}\n"
        f'goal: "fixture {sid}"\n'
        "metric: m\n"
        "mode: fight\n"
        "methodology:\n"
        '  approach: "x"\n'
        "  evidence: []\n"
        "  primary_change:\n"
        "    type: add\n"
        "    node: execute\n"
        '    baseline: "b"\n'
        '    expected_band: "WIN if x"\n'
        '    rollback: "git revert"\n'
        f'    eval_window: "{sid}"\n'
        "  pipeline:\n"
        "    - phase: execute\n"
        "      primitive: execute\n"
        "      agents: writers\n"
        "      prompt: prompts/dev/dummy.md\n"
        "      writes: results.jsonl\n"
    )


def _s123_campaign(tmp_path: Path, sid: str = "s122") -> Path:
    """A tmp campaign holding one latest season; the state-dir root.

    root is the state dir draft_next resolves through paths.seasons_dir
    (the engine convention). The real campaign is never touched.
    """
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    season = root / "seasons" / f"{sid}.yaml"
    season.write_text(_s123_season_text(sid), encoding="utf-8")
    return root


def _s123_plan(caplog: pytest.LogCaptureFixture, root: Path, parent_id: str) -> str:
    """Plan the next season from parent_id; the draft must land; return the log."""
    with caplog.at_level(logging.DEBUG, logger="rumpun.evolve"):
        drafted = evolve.draft_next(root, root / "seasons" / f"{parent_id}.yaml")
    assert drafted.is_file(), f"the plan never produced the draft: {drafted}"
    return caplog.text


def test_s123_pin1_plan_names_loop_draft(tmp_path: Path, caplog: Any) -> None:
    """Red-first: the loop's draft for the next id makes the plan name its path.

    The s120 close-prep hand-off lands the loop's draft at
    runs/<parent>/seasons/<next>.yaml. With that file present, the plan of
    s123 from s122 warns naming that path and still drafts: the hint never
    blocks (the s116 warning pattern).
    """
    root = _s123_campaign(tmp_path)
    loop_draft = root / "runs" / "s122" / "seasons" / "s123.yaml"
    loop_draft.parent.mkdir(parents=True)
    loop_draft.write_text("id: s123\n", encoding="utf-8")
    text = _s123_plan(caplog, root, "s122")
    assert "loop draft" in text, f"the plan stayed silent about the hand-off: {text!r}"
    assert str(loop_draft) in text, f"the hint never names the path: {text!r}"
    assert (root / "seasons" / "s123.yaml").is_file(), (
        "the hint blocked the planner's own draft"
    )


def test_s123_pin2_wrong_id_stays_silent(tmp_path: Path, caplog: Any) -> None:
    """Green guard: a staged draft under a different id never triggers the hint.

    runs/s122/seasons/s124.yaml is not a draft of the next id (s123): a
    stale or unrelated staged file must not send the worker to fill it.
    """
    root = _s123_campaign(tmp_path)
    stale = root / "runs" / "s122" / "seasons" / "s124.yaml"
    stale.parent.mkdir(parents=True)
    stale.write_text("id: s124\n", encoding="utf-8")
    text = _s123_plan(caplog, root, "s122")
    assert "loop draft" not in text, f"the plan fired on a wrong id: {text!r}"


def test_s123_pin3_no_loop_tree_stays_silent(tmp_path: Path, caplog: Any) -> None:
    """Green guard: no loop run tree, no hint.

    A campaign that never ran the loop holds no runs/<parent>/seasons/
    draft; the plan drafts plain and says nothing about a hand-off.
    """
    root = _s123_campaign(tmp_path)
    text = _s123_plan(caplog, root, "s122")
    assert "loop draft" not in text, f"the plan invented a hand-off: {text!r}"


def test_s123_pin4_guide_states_lane_commit_rule() -> None:
    """Red-first: the campaign guide's close section states the rule.

    Every rule token appears in docs/campaign-guide.md inside the close
    section (after ## 3. Close the season), and the close names its paths --
    the pathspec form, amended at the s123 close after the four-review
    pass: the wide add taught the sibling-sweep vector.
    """
    text = _s123_norm(GUIDE.read_text(encoding="utf-8"))
    close_at = text.index("## 3. Close the season")
    for token in _S123_RULE_TOKENS:
        assert token in text, f"the guide never states {token!r}"
        assert text.index(token) > close_at, f"{token!r} sits before the close section"
    assert "git add -A" not in text[close_at:], "the close still teaches the wide add"
    assert "-- <paths>" in text[close_at:], "the close commit lost the pathspec form"


def test_s123_pin5_readme_states_lane_commit_rule() -> None:
    """Red-first: the README lifecycle section states the rule.

    Every rule token appears between ## Season lifecycle and the next ##
    heading, nowhere else required.
    """
    text = _s123_norm(README.read_text(encoding="utf-8"))
    head = text.index("## Season lifecycle")
    tail = text.index("## ", head + 1)
    section = text[head:tail]
    for token in _S123_RULE_TOKENS:
        assert token in section, f"the README lifecycle never states {token!r}"
