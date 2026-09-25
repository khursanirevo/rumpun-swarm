"""s134 w2 pins: the scaffold asks for the notes; shipped directives get marked.

Spec source: the s134 w2 brief (.rumpun/runs/s134/w2/prompt.md) and filed
issues #46/#48 on khursanirevo/rumpun. Two lifecycle-end defects, one lane:

- issue #46: the s112 close gate (engine._agent_snap) marks every exited
  writer whose workspace lacks notes.md `incomplete: notes.md missing`,
  but the scaffolded writer prompt contracts (scaffold.PROMPTS) never ask
  writers for it. Fix: execute.md and evaluate.md gain the exit contract
  (the gate and the prompts agree).
- issue #48: directives.jsonl rows keep status pending after the named
  work ships. Fix: the reader-derived shipped mark. A pending row whose
  `evidence` names only artifacts that exist in the tree reads shipped
  (evolve.directive_statuses); draft_next names those rows at plan time,
  and the loop's close-prep drafts through draft_next, so the same mark
  rides the loop. The queue file is never rewritten: the mark is the
  reader's, append-only holds.

Fixture discipline: tmp campaigns only; the real directives.jsonl is
never written in tests; akar records land only in the tmp ledger.

Red-first honesty: RED captured 2026-09-21 pre-implementation,
/tmp/s134-w2-pins-red.txt -- 11 failed, 1 passed (the silence pin green
on arrival by design; its positive control is pin11 in the same run).
GREEN captured 2026-09-21 post-implementation,
/tmp/s134-w2-pins-green.txt -- 12 passed.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import pytest

from rumpun import akar, collab, evolve, scaffold, yamlio


def _s134_campaign(tmp_path: Path) -> Path:
    """Tmp campaign root (the .rumpun dir) with the ledger tree present.

    The ledger/ dir exists up front so paths.ledger_dir resolves the new
    name for both the fixture writer and directive_statuses.
    """
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    return root


def _s134_lane(root: Path) -> dict[str, str]:
    """The P8 directives lane, same shape the cli builds."""
    ledger = root / "ledger"
    return {
        "file": str(ledger / "directives.jsonl"),
        "lock": str(ledger / "directives.lock"),
    }


def _s134_directive(
    root: Path,
    text: str,
    status: str = "pending",
    evidence: object = None,
) -> dict:
    """Append one directive row to the tmp campaign's lane."""
    payload: dict = {"text": text, "status": status}
    if evidence is not None:
        payload["evidence"] = evidence
    return collab.append_event(_s134_lane(root), "operator", payload)


def _s134_touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("landed\n", encoding="utf-8")
    return path


def _s134_season_text(sid: str, parent_id: str | None) -> str:
    """One draftable lineage season (the s132 fixture shape)."""
    lines = [
        f"id: {sid}",
        f'goal: "fixture {sid}"',
        "metric: m",
        "mode: fight",
        "methodology:",
        '  approach: "x"',
        "  evidence: []",
        "  primary_change:",
        "    type: add",
        "    node: execute",
        '    baseline: "b"',
        '    expected_band: "WIN if x"',
        '    rollback: "git revert"',
        f'    eval_window: "{sid}"',
        "  pipeline:",
        "    - phase: execute",
        "      primitive: execute",
        "      agents: writers",
        "      prompt: prompts/dev/dummy.md",
        "      writes: results.jsonl",
    ]
    if parent_id is not None:
        lines.insert(1, f"parent: {parent_id}")
    return "\n".join(lines) + "\n"


def _s134_plan(caplog: pytest.LogCaptureFixture, root: Path) -> str:
    """Plan s2 from s1; the draft must land (the mark never blocks)."""
    with caplog.at_level(logging.WARNING, logger="rumpun.evolve"):
        drafted = evolve.draft_next(root, root / "seasons" / "s1.yaml")
    assert drafted.is_file(), f"the plan never produced the draft: {drafted}"
    return caplog.text


def _s134_scaffold(tmp_path: Path) -> Path:
    """A freshly scaffolded campaign; returns its .rumpun dir."""
    proj = tmp_path / "scaffolded"
    scaffold.init_project(proj)
    return proj / ".rumpun"


# --- issue #46: the scaffolded writer prompts ask for notes.md ----------


def test_s134_pin01_execute_prompt_asks_for_notes(
    tmp_path: Path,
) -> None:
    """The scaffolded execute.md exit contract names notes.md."""
    dot = _s134_scaffold(tmp_path)
    text = (dot / "prompts" / "base" / "execute.md").read_text(encoding="utf-8")
    assert "notes.md" in text, "execute.md never asks the writer for notes.md"


def test_s134_pin02_evaluate_prompt_asks_for_notes(
    tmp_path: Path,
) -> None:
    """The scaffolded evaluate.md exit contract names notes.md."""
    dot = _s134_scaffold(tmp_path)
    text = (dot / "prompts" / "base" / "evaluate.md").read_text(encoding="utf-8")
    assert "notes.md" in text, "evaluate.md never asks the writer for notes.md"


def test_s134_pin03_template_writer_prompts_carry_the_clause(
    tmp_path: Path,
) -> None:
    """Every writer prompt the shipped season templates reference names notes.md.

    The gate applies to every exited writer workspace, so the invariant is
    over the templates' writers[].prompt files, not just the two names the
    current templates happen to use.
    """
    for label, template_text in (
        ("SEASON_S1", scaffold.SEASON_S1),
        ("COMPETITION_TEMPLATE", scaffold.COMPETITION_TEMPLATE),
    ):
        template_path = tmp_path / f"{label}.yaml"
        template_path.write_text(template_text, encoding="utf-8")
        doc = yamlio.load(template_path)
        for writer in doc.get("writers", []):
            stem = Path(writer["prompt"]).stem
            assert stem in scaffold.PROMPTS, (
                f"{label} writer {writer.get('name')} references "
                f"unshipped prompt {writer['prompt']}"
            )
            assert "notes.md" in scaffold.PROMPTS[stem], (
                f"{label} writer prompt {stem}.md never asks for notes.md"
            )


# --- issue #48: directives.jsonl gains the shipped marking --------------


def test_s134_pin04_missing_lane_reads_empty(tmp_path: Path) -> None:
    """A campaign with no directives.jsonl reads an empty mark set."""
    root = _s134_campaign(tmp_path)
    assert evolve.directive_statuses(root) == []


def test_s134_pin05_pending_with_existing_evidence_reads_shipped(
    tmp_path: Path,
) -> None:
    """A pending row whose named evidence file exists reads shipped."""
    root = _s134_campaign(tmp_path)
    _s134_touch(root.parent / "handoff.md")
    _s134_directive(root, "absorb the handoff", evidence="handoff.md")
    rows = evolve.directive_statuses(root)
    assert len(rows) == 1
    assert rows[0]["status"] == "pending"  # the written status stays
    assert rows[0]["effective_status"] == "shipped"


def test_s134_pin06_pending_without_evidence_stays_pending(
    tmp_path: Path,
) -> None:
    """A row with no evidence key reads exactly as written."""
    root = _s134_campaign(tmp_path)
    _s134_directive(root, "plain pending work")
    rows = evolve.directive_statuses(root)
    assert rows[0]["effective_status"] == "pending"


def test_s134_pin07_pending_with_missing_evidence_stays_pending(
    tmp_path: Path,
) -> None:
    """A pending row whose named evidence is absent stays pending."""
    root = _s134_campaign(tmp_path)
    _s134_directive(root, "not landed yet", evidence="absent/thing.md")
    rows = evolve.directive_statuses(root)
    assert rows[0]["effective_status"] == "pending"


def test_s134_pin08_evidence_list_all_or_nothing(tmp_path: Path) -> None:
    """List evidence ships only when every named artifact exists."""
    root = _s134_campaign(tmp_path)
    _s134_touch(root.parent / "src" / "rumpun" / "landed.py")
    _s134_touch(root.parent / "docs" / "landed.md")
    _s134_directive(
        root, "ship the module", evidence=["src/rumpun/landed.py", "docs/landed.md"]
    )
    _s134_directive(
        root,
        "ship the module, second leg missing",
        evidence=["src/rumpun/landed.py", "docs/absent.md"],
    )
    rows = {row["seq"]: row for row in evolve.directive_statuses(root)}
    assert rows[0]["effective_status"] == "shipped"
    assert rows[1]["effective_status"] == "pending"


def test_s134_pin09_ledger_citation_reads_shipped(tmp_path: Path) -> None:
    """A ledger: citation ships on the record; a named digest must match.

    The digest is the record's sha256 body trailer, exact or unambiguous
    prefix, the citation shape the ledger already uses
    (ledger:s80-harvest@ed4d22e4...).
    """
    root = _s134_campaign(tmp_path)
    body = "the named work landed and was live-verified"
    assert akar.append_record(root, "s80-harvest", "the harvest", body).is_file()
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    _s134_directive(root, "keep the standard", evidence=f"ledger:s80-harvest@{digest}")
    _s134_directive(root, "wrong digest", evidence=f"ledger:s80-harvest@{'0' * 64}")
    _s134_directive(root, "unknown record", evidence="ledger:absent-record")
    _s134_directive(root, "plain citation", evidence="ledger:s80-harvest")
    rows = {row["seq"]: row for row in evolve.directive_statuses(root)}
    assert rows[0]["effective_status"] == "shipped"
    assert rows[1]["effective_status"] == "pending"
    assert rows[2]["effective_status"] == "pending"
    assert rows[3]["effective_status"] == "shipped"


def test_s134_pin10_consumed_never_rederived(tmp_path: Path) -> None:
    """Non-pending rows read as written; empty-string evidence stays pending."""
    root = _s134_campaign(tmp_path)
    _s134_touch(root.parent / "landed.md")
    _s134_directive(root, "out-of-band ship", status="consumed")
    _s134_directive(
        root, "consumed with evidence", status="consumed", evidence="landed.md"
    )
    _s134_directive(root, "pending, empty evidence", evidence="")
    rows = {row["seq"]: row for row in evolve.directive_statuses(root)}
    assert rows[0]["effective_status"] == "consumed"
    assert rows[1]["effective_status"] == "consumed"
    assert rows[2]["effective_status"] == "pending"


def test_s134_pin11_plan_surfaces_shipped_directive(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The plan names the rows that now read shipped; the draft still lands."""
    root = _s134_campaign(tmp_path)
    season = root / "seasons" / "s1.yaml"
    season.write_text(_s134_season_text("s1", None), encoding="utf-8")
    _s134_touch(root.parent / "src" / "rumpun" / "landed.py")
    _s134_directive(root, "ship the landed module", evidence="src/rumpun/landed.py")
    log = _s134_plan(caplog, root)
    assert "seq 0 reads shipped" in log
    assert "src/rumpun/landed.py" in log


def test_s134_pin12_plan_silent_without_directives_file(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """No directives file: the plan drafts on, announcing nothing."""
    root = _s134_campaign(tmp_path)
    season = root / "seasons" / "s1.yaml"
    season.write_text(_s134_season_text("s1", None), encoding="utf-8")
    log = _s134_plan(caplog, root)
    assert "reads shipped" not in log
